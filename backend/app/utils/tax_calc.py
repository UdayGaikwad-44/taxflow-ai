"""
Tax calculation utilities for FY 2025-26 (New Tax Regime).
Moved here from routes/tax.py so it can be imported by other routes and services
without creating circular route-to-route imports.
"""


def calculate_tax(income: float) -> float:
    """
    FY 2025-26 new regime tax slabs + 4% cess.
    Section 87A rebate: net income ≤ ₹12,00,000 → zero tax.

    Slabs (after standard deduction of ₹75,000 for salaried):
        0  – 4,00,000    : 0%
        4L – 8L          : 5%
        8L – 12L         : 10%
        12L – 16L        : 15%
        16L – 20L        : 20%
        20L – 24L        : 25%
        > 24L            : 30%
    """
    income = max(0.0, float(income))
    if income <= 1_200_000:
        # Section 87A rebate covers full tax up to ₹12L
        return 0.0

    slabs = [
        (400_000, 0.00),
        (800_000, 0.05),
        (1_200_000, 0.10),
        (1_600_000, 0.15),
        (2_000_000, 0.20),
        (2_400_000, 0.25),
        (float("inf"), 0.30),
    ]

    tax = 0.0
    prev = 0.0
    remaining = income
    for upper, rate in slabs:
        slab_size = upper - prev
        if remaining <= 0:
            break
        taxable = min(remaining, slab_size)
        tax += taxable * rate
        remaining -= taxable
        prev = upper

    # 4% health & education cess
    return round(tax * 1.04, 2)
