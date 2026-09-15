"""
Power calculation: how many molecules needed to detect the 17.6pp quantum vs coined RW
advantage at 80% power, α=0.05 (one-sided)?

Two distinct tests:
  Test A — Accuracy comparison (two independent proportions):
           H0: p_Q = p_Coined  vs  H1: p_Q - p_Coined = 0.176
           This is the main claim: "quantum is more accurate"
  Test B — Head-to-head binomial (non-tied comparisons only):
           H0: P(Q wins | non-tied) = 0.5  vs  H1: > 0.5
           This is stricter — only molecules where methods disagree

We compute both.
"""
from math import sqrt
from scipy.stats import norm, binom

# ---------------------------------------------------------------------------
# Observed parameters from our data (n=17)
# ---------------------------------------------------------------------------
Q_ACCURACY       = 15/17          # 0.882
COINED_ACCURACY  = 12/17         # 0.706
EFFECT_SIZE      = Q_ACCURACY - COINED_ACCURACY   # 0.176 (17.6 pp)

# In our data, 6/17 comparisons are non-tied
OBSERVED_NONTIED_RATE = 6/17   # 0.353
# And 4/6 of those non-tied go to quantum
OBSERVED_Q_WIN_GIVEN_NONTIED = 4/6  # 0.667

print("=" * 70)
print("POWER CALCULATION: Quantum Walk vs Coined RW")
print("=" * 70)
print(f"\nObserved parameters (n=17 pilot):")
print(f"  Quantum accuracy:        {Q_ACCURACY:.1%}")
print(f"  Coined RW accuracy:     {COINED_ACCURACY:.1%}")
print(f"  Accuracy gap:           {EFFECT_SIZE:.1%} ({100*EFFECT_SIZE:.1f} pp)")
print(f"  Non-tied rate:          {OBSERVED_NONTIED_RATE:.1%}  ({int(OBSERVED_NONTIED_RATE*17)}/{17})")
print(f"  Q win rate (non-tied):  {OBSERVED_Q_WIN_GIVEN_NONTIED:.1%}  ({int(OBSERVED_Q_WIN_GIVEN_NONTIED*6)}/6)")


# ==========================================================================
# TEST A: Two-proportion z-test (accuracy comparison)
# ==========================================================================
# For comparing two independent proportions: p_Q vs p_C
# H0: p_Q - p_C = 0   vs   H1: p_Q - p_C = delta > 0
# n per group needed at α=0.05 (one-sided), power=80%
alpha   = 0.05
beta    = 0.20
z_alpha = norm.ppf(1 - alpha)    # 1.645
z_beta  = norm.ppf(1 - beta)     # 0.842

p_Q = Q_ACCURACY
p_C = COINED_ACCURACY
delta = p_Q - p_C   # 0.176

# Two-proportion formula (Schaffer, 1975; fleet approximation)
# n = [(z_alpha*sqrt(2*p_bar*q_bar) + z_beta*sqrt(p_Q*q_Q + p_C*q_C))^2] / delta^2
p_bar = (p_Q + p_C) / 2
q_bar = 1 - p_bar

n_per_group = ((z_alpha * sqrt(2*p_bar*q_bar) + z_beta * sqrt(p_Q*(1-p_Q) + p_C*(1-p_C)))**2) / delta**2
n_total_ztest = 2 * n_per_group

print(f"\n" + "=" * 70)
print("TEST A: TWO-PROPORTION ACCURACY COMPARISON")
print("=" * 70)
print(f"  H0: p_Q = p_Coined  (both equally accurate)")
print(f"  H1: p_Q - p_Coined = {delta:.3f}  ({delta:.1%} absolute gap)")
print(f"  α = {alpha} (one-sided), power = {1-beta:.0%}")
print(f"  Formula: two-proportion z-test (Schaffer approximation)")
print(f"\n  Per group: n ≈ {n_per_group:.0f}")
print(f"  Total molecules needed (both groups): n ≈ {n_total_ztest:.0f}")
print(f"\n  → Rounded up: n = {int(n_total_ztest) + 10} molecules total")
print(f"\n  Interpretation: With ~{int(n_total_ztest)+10} molecules, a two-proportion")
print(f"  z-test will detect the 17.6pp accuracy gap at 80% power.")


# ==========================================================================
# TEST B: Head-to-head binomial (non-tied comparisons only)
# ==========================================================================
print(f"\n" + "=" * 70)
print("TEST B: HEAD-TO-HEAD BINOMIAL (non-tied comparisons only)")
print("=" * 70)
print(f"  Only molecules where exactly one method is correct contribute")
print(f"  to the test — ties (both correct / both wrong) are excluded.")
print(f"  H0: P(Q wins | non-tied) = 0.5")
print(f"  H1: P(Q wins | non-tied) = {OBSERVED_Q_WIN_GIVEN_NONTIED:.3f}")

# Exact binomial power (verified against simulation)
def exact_power_binomial(n, p1, alpha=0.05):
    """Exact binomial power for H0: p=0.5, H1: p=p1, one-sided."""
    # Find critical value k_alpha: smallest k where P(X >= k | p=0.5) <= alpha
    k_alpha = n
    for k in range(n + 1):
        tail = sum(binom.pmf(j, n, 0.5) for j in range(k, n + 1))
        if tail <= alpha:
            k_alpha = k
            break
    # Power: P(X >= k_alpha | p=p1)
    power = sum(binom.pmf(j, n, p1) for j in range(k_alpha, n + 1))
    return k_alpha, power

print(f"\n  Exact binomial power at various n (non-tied comparisons):")
for n in [20, 30, 40, 50, 60, 70, 80, 90, 100, 110, 120, 140, 160]:
    k_alpha, power = exact_power_binomial(n, OBSERVED_Q_WIN_GIVEN_NONTIED)
    marker = " ← 80%" if 0.78 <= power <= 0.82 else ""
    print(f"    n={n:3d}: k_α={k_alpha:2d}, power={power:.1%}{marker}")

# Find n for ~80% power
for n in range(50, 200):
    _, power = exact_power_binomial(n, OBSERVED_Q_WIN_GIVEN_NONTIED)
    if abs(power - 0.80) < 0.02:
        print(f"\n  → n ≈ {n} non-tied comparisons gives power ≈ {power:.1%}")
        break

# Back-convert to total molecules
NONTIED_RATE = OBSERVED_NONTIED_RATE
n_nontied_needed = 0
for n in range(50, 200):
    _, power = exact_power_binomial(n, OBSERVED_Q_WIN_GIVEN_NONTIED)
    if power >= 0.80:
        n_nontied_needed = n
        break

n_total_both = int(n_nontied_needed / NONTIED_RATE) + 1
print(f"\n  With observed non-tied rate = {OBSERVED_NONTIED_RATE:.1%}:")
print(f"  Non-tied comparisons needed: ≈ {n_nontied_needed}")
print(f"  → Total molecules needed: ≈ {n_total_both}")


# ==========================================================================
# SENSITIVITY TABLE
# ==========================================================================
print(f"\n" + "=" * 70)
print("SENSITIVITY: total n needed for 80% power at various non-tied rates")
print("=" * 70)
print(f"  {'Non-tied rate':<20} {'n (Test A)':>12} {'n (Test B)':>12}")
print(f"  {'-'*20} {'-'*12} {'-'*12}")

# Test A doesn't depend on non-tied rate (it's a proportion test)
for rate in [0.20, 0.25, 0.30, 0.35, 0.40]:
    n_b = int(n_nontied_needed / rate) + 1
    print(f"  {rate:.0%}{'':15} {'~'+str(int(n_total_ztest)):>12} {n_b:>12}")


# ==========================================================================
# SUMMARY
# ==========================================================================
print(f"\n" + "=" * 70)
print("CONCLUSION")
print("=" * 70)
print(f"""
Two distinct tests, two different n targets:

TEST A — Accuracy gap (two-proportion z-test):
  Detecting the 17.6pp accuracy gap (88.2% vs 70.6%)
  at 80% power, α=0.05 (one-sided):
  → n = {int(n_total_ztest)+10} molecules total

TEST B — Head-to-head binomial (non-tied only):
  Detecting P(Q wins | non-tied) = 0.667 vs 0.5:
  → n = {n_total_both} molecules (at {OBSERVED_NONTIED_RATE:.0%} non-tied rate)

RECOMMENDATION:
  The accuracy gap test (Test A) is the primary scientific claim
  ("quantum walk is more accurate than classical methods").
  n = {int(n_total_ztest)+10} ≈ {int(n_total_ztest/10)*10} is the right target.

  Note: {int(n_total_ztest)+10} total means ~{int(n_total_ztest/2)+5} per group
  (quantum vs coined RW), which is achievable with the PAH + alkane
  homologous series plus additional heterocycles.

  The non-tied rate ({OBSERVED_NONTIED_RATE:.0%}) is a ceiling — as we add more
  diverse molecules, ties may decrease, which would REDUCE n needed.
""")
