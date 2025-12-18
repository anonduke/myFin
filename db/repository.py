from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Iterable, List, Optional

from db.connection import get_connection, init_db
from core.utils import format_date, parse_date
from models.types import CreditCard, Debt, FxRate, SavingsAccount


@dataclass(frozen=True)
class PaymentRecord:
    id: int
    payment_date: date
    target_type: str
    target_id: int
    payment_amount_original: float
    payment_currency: str
    payment_amount_cad: float
    applied_penal: float
    applied_interest: float
    applied_principal: float


@dataclass(frozen=True)
class MonthlySnapshot:
    snapshot_date: date
    total_debt_cad: float
    total_interest_cad: float
    total_savings_cad: float
    net_position_cad: float


class Repository:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        init_db(db_path)

    def _connect(self):
        return get_connection(self.db_path)

    def add_debt(self, debt: Debt) -> int:
        with self._connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO debts (
                    lender_name, debt_type, original_currency, principal_original,
                    principal_outstanding_cad, interest_rate_annual, penal_rate_annual,
                    loan_start_date, installment_amount, installment_due_day,
                    last_payment_date, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    debt.lender_name,
                    debt.debt_type,
                    debt.original_currency,
                    debt.principal_original,
                    debt.principal_outstanding_cad,
                    debt.interest_rate_annual,
                    debt.penal_rate_annual,
                    format_date(debt.loan_start_date),
                    debt.installment_amount,
                    debt.installment_due_day,
                    format_date(debt.last_payment_date) if debt.last_payment_date else None,
                    debt.status,
                ),
            )
            return int(cursor.lastrowid)

    def list_debts(self, status: Optional[str] = None) -> List[Debt]:
        with self._connect() as conn:
            if status:
                rows = conn.execute("SELECT * FROM debts WHERE status = ?", (status,)).fetchall()
            else:
                rows = conn.execute("SELECT * FROM debts").fetchall()

        return [
            Debt(
                id=row["id"],
                lender_name=row["lender_name"],
                debt_type=row["debt_type"],
                original_currency=row["original_currency"],
                principal_original=row["principal_original"],
                principal_outstanding_cad=row["principal_outstanding_cad"],
                interest_rate_annual=row["interest_rate_annual"],
                penal_rate_annual=row["penal_rate_annual"],
                loan_start_date=parse_date(row["loan_start_date"]),
                installment_amount=row["installment_amount"],
                installment_due_day=row["installment_due_day"],
                last_payment_date=parse_date(row["last_payment_date"]),
                status=row["status"],
            )
            for row in rows
        ]

    def update_debt_principal(self, debt_id: int, principal_outstanding_cad: float) -> None:
        with self._connect() as conn:
            conn.execute(
                "UPDATE debts SET principal_outstanding_cad = ? WHERE id = ?",
                (principal_outstanding_cad, debt_id),
            )

    def update_debt_last_payment(self, debt_id: int, last_payment_date: date) -> None:
        with self._connect() as conn:
            conn.execute(
                "UPDATE debts SET last_payment_date = ? WHERE id = ?",
                (format_date(last_payment_date), debt_id),
            )

    def add_credit_card(self, card: CreditCard) -> int:
        with self._connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO credit_cards (
                    bank_name, card_name, credit_limit_cad, statement_balance_cad,
                    interest_rate_annual, statement_date, due_date, last_payment_date,
                    flat_late_fee_cad, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    card.bank_name,
                    card.card_name,
                    card.credit_limit_cad,
                    card.statement_balance_cad,
                    card.interest_rate_annual,
                    format_date(card.statement_date),
                    format_date(card.due_date),
                    format_date(card.last_payment_date) if card.last_payment_date else None,
                    card.flat_late_fee_cad,
                    card.status,
                ),
            )
            return int(cursor.lastrowid)

    def list_credit_cards(self, status: Optional[str] = None) -> List[CreditCard]:
        with self._connect() as conn:
            if status:
                rows = conn.execute("SELECT * FROM credit_cards WHERE status = ?", (status,)).fetchall()
            else:
                rows = conn.execute("SELECT * FROM credit_cards").fetchall()

        return [
            CreditCard(
                id=row["id"],
                bank_name=row["bank_name"],
                card_name=row["card_name"],
                credit_limit_cad=row["credit_limit_cad"],
                statement_balance_cad=row["statement_balance_cad"],
                interest_rate_annual=row["interest_rate_annual"],
                statement_date=parse_date(row["statement_date"]),
                due_date=parse_date(row["due_date"]),
                last_payment_date=parse_date(row["last_payment_date"]),
                flat_late_fee_cad=row["flat_late_fee_cad"],
                status=row["status"],
            )
            for row in rows
        ]

    def update_credit_card_balance(self, card_id: int, statement_balance_cad: float) -> None:
        with self._connect() as conn:
            conn.execute(
                "UPDATE credit_cards SET statement_balance_cad = ? WHERE id = ?",
                (statement_balance_cad, card_id),
            )

    def update_credit_card_last_payment(self, card_id: int, last_payment_date: date) -> None:
        with self._connect() as conn:
            conn.execute(
                "UPDATE credit_cards SET last_payment_date = ? WHERE id = ?",
                (format_date(last_payment_date), card_id),
            )

    def add_payment(
        self,
        payment_date: date,
        target_type: str,
        target_id: int,
        payment_amount_original: float,
        payment_currency: str,
        payment_amount_cad: float,
        applied_penal: float,
        applied_interest: float,
        applied_principal: float,
    ) -> int:
        with self._connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO payments (
                    payment_date, target_type, target_id, payment_amount_original,
                    payment_currency, payment_amount_cad, applied_penal,
                    applied_interest, applied_principal
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    format_date(payment_date),
                    target_type,
                    target_id,
                    payment_amount_original,
                    payment_currency,
                    payment_amount_cad,
                    applied_penal,
                    applied_interest,
                    applied_principal,
                ),
            )
            return int(cursor.lastrowid)

    def list_payments(self, target_type: Optional[str] = None, target_id: Optional[int] = None) -> List[PaymentRecord]:
        query = "SELECT * FROM payments"
        params: List[object] = []
        clauses = []
        if target_type:
            clauses.append("target_type = ?")
            params.append(target_type)
        if target_id is not None:
            clauses.append("target_id = ?")
            params.append(target_id)
        if clauses:
            query += " WHERE " + " AND ".join(clauses)
        query += " ORDER BY payment_date DESC"

        with self._connect() as conn:
            rows = conn.execute(query, tuple(params)).fetchall()

        return [
            PaymentRecord(
                id=row["id"],
                payment_date=parse_date(row["payment_date"]),
                target_type=row["target_type"],
                target_id=row["target_id"],
                payment_amount_original=row["payment_amount_original"],
                payment_currency=row["payment_currency"],
                payment_amount_cad=row["payment_amount_cad"],
                applied_penal=row["applied_penal"],
                applied_interest=row["applied_interest"],
                applied_principal=row["applied_principal"],
            )
            for row in rows
        ]

    def add_savings_account(self, account_name: str, currency: str, balance_cad: float) -> int:
        with self._connect() as conn:
            cursor = conn.execute(
                "INSERT INTO savings (account_name, currency, balance_cad) VALUES (?, ?, ?)",
                (account_name, currency, balance_cad),
            )
            return int(cursor.lastrowid)

    def list_savings(self) -> List[SavingsAccount]:
        with self._connect() as conn:
            rows = conn.execute("SELECT * FROM savings").fetchall()
        return [
            SavingsAccount(
                id=row["id"],
                account_name=row["account_name"],
                currency=row["currency"],
                balance_cad=row["balance_cad"],
            )
            for row in rows
        ]

    def upsert_fx_rate(self, rate: FxRate) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO fx_rates (currency, rate_to_cad, last_updated, source)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(currency) DO UPDATE SET
                    rate_to_cad = excluded.rate_to_cad,
                    last_updated = excluded.last_updated,
                    source = excluded.source
                """,
                (rate.currency, rate.rate_to_cad, format_date(rate.last_updated), rate.source),
            )

    def get_fx_rate(self, currency: str) -> Optional[FxRate]:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM fx_rates WHERE currency = ?", (currency.upper(),)).fetchone()
        if not row:
            return None
        return FxRate(
            currency=row["currency"],
            rate_to_cad=row["rate_to_cad"],
            last_updated=parse_date(row["last_updated"]),
            source=row["source"],
        )

    def list_fx_rates(self) -> List[FxRate]:
        with self._connect() as conn:
            rows = conn.execute("SELECT * FROM fx_rates").fetchall()
        return [
            FxRate(
                currency=row["currency"],
                rate_to_cad=row["rate_to_cad"],
                last_updated=parse_date(row["last_updated"]),
                source=row["source"],
            )
            for row in rows
        ]

    def add_monthly_snapshot(self, snapshot: MonthlySnapshot) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO monthly_snapshots (
                    snapshot_date, total_debt_cad, total_interest_cad,
                    total_savings_cad, net_position_cad
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (
                    format_date(snapshot.snapshot_date),
                    snapshot.total_debt_cad,
                    snapshot.total_interest_cad,
                    snapshot.total_savings_cad,
                    snapshot.net_position_cad,
                ),
            )

    def list_monthly_snapshots(self) -> List[MonthlySnapshot]:
        with self._connect() as conn:
            rows = conn.execute("SELECT * FROM monthly_snapshots ORDER BY snapshot_date DESC").fetchall()
        return [
            MonthlySnapshot(
                snapshot_date=parse_date(row["snapshot_date"]),
                total_debt_cad=row["total_debt_cad"],
                total_interest_cad=row["total_interest_cad"],
                total_savings_cad=row["total_savings_cad"],
                net_position_cad=row["net_position_cad"],
            )
            for row in rows
        ]
