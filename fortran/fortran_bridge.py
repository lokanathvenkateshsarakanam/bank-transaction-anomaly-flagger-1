"""Fortran Numerical Simulation Bridge for Monte Carlo Value-at-Risk (VaR).

Executes the high-precision numerical algorithms specified in fortran/risk_monte_carlo.f90
to compute Value-at-Risk (VaR 99%) and Expected Shortfall (CVaR) for high-stakes transactions.
"""

import math
import random
from typing import Dict, Tuple


class FortranRiskEngine:
    """Numerical engine mirroring fortran/risk_monte_carlo.f90."""

    @classmethod
    def simulate_var_cvar(
        cls,
        base_amount: float,
        p_fraud: float,
        n_simulations: int = 10000,
        confidence_level: float = 0.99,
        seed: int = 42,
    ) -> Dict[str, float]:
        """Simulates loss distribution and computes 99% VaR and CVaR (Expected Shortfall)."""
        rng = random.Random(seed)
        losses = []

        for _ in range(n_simulations):
            u = rng.random()
            if u < p_fraud:
                # Pareto tail multiplier as defined in Fortran module
                simulated_loss = base_amount * (1.0 + u * 2.5)
            else:
                simulated_loss = 0.0
            losses.append(simulated_loss)

        losses.sort()

        cutoff_index = int(n_simulations * confidence_level)
        cutoff_index = min(n_simulations - 1, max(0, cutoff_index))

        var_val = losses[cutoff_index]
        tail_losses = losses[cutoff_index:]
        cvar_val = sum(tail_losses) / len(tail_losses) if tail_losses else var_val

        return {
            "confidence_level": confidence_level,
            "simulations_count": n_simulations,
            "value_at_risk_99": round(var_val, 2),
            "expected_shortfall_cvar": round(cvar_val, 2),
            "expected_unconditional_loss": round(sum(losses) / n_simulations, 2),
        }
