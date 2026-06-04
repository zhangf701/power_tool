# PowerTool Manual - Parameter Validation & Per-Unit: Lines

## 1. Purpose
This page converts named line parameters into per-unit values and checks whether the inputs lie in typical engineering ranges. The line-geometry calculator includes two calculation pages: overhead-line parameters and cable parameters.

## 2. Suggested Workflow
1. Enter the system base values, line length, and positive-/zero-sequence parameters.
2. Run the calculation and review the physical-unit summary and per-unit summary.
3. If parameters need to be derived from geometry, open **Line Parameter Calculation** and choose either **Overhead Line Parameter Calculation** or **Cable Parameter Calculation**.
4. For cable studies, enter conductor, insulation, burial, sheath/screen, and sheath-bonding data, then review the reported zero-sequence return model.

## 3. Cable Zero-Sequence Return Logic
The cable page follows an automatic engineering rule by default:

- No metallic sheath/screen, or single-point bonding: use earth return.
- Both-end bonding: use sheath-plus-earth return with multi-conductor matrix reduction.
- Cross-bonding: use the same sheath-plus-earth Kron-reduction approximation, with a note that steady-state sheath circulating losses are reduced by cross-bonding.

This is closer to PSCAD line-constants practice than a fixed `X0/X1` rule: the program first builds a simplified multi-conductor system for the three cores and three metallic sheaths, then eliminates the sheath conductors with Kron reduction. The advanced override can force earth return, sheath-only coaxial lower-bound return, or sheath-plus-earth return when checking special cases.

## 4. Interpreting `X0 < X1`
`X0 < X1` is not assumed for all cables. It can appear when a bonded metallic sheath or screen provides a close zero-sequence return path and partially cancels the external magnetic field. If the sheath is single-point bonded, absent, poorly bonded, or if the relevant return path is mainly earth/grid/ECC, `X0` can become much larger than `X1`.

Use manufacturer sequence-impedance data, measured values, or a formal line-constants tool for relay settings, commissioning decisions, or unusual cable structures such as pipe-type cables, three-core armored cables, long cross-bonded sections, or routes with strong adjacent metallic return paths.

## 5. What to Check Carefully
- Base voltage and base capacity must match the intended study base.
- Sequence resistance, reactance, and capacitance should use consistent units.
- Cable sheath resistance and radius strongly affect zero-sequence results.
- The result note block states whether the zero-sequence model was inferred automatically or forced by the advanced override.
- Treat three-core common-sheath/armored cables as a separate structure rather than directly reusing the single-core sheath model.

## 6. Common Mistakes
- Confusing Ω/km with total Ω.
- Mixing microfarads and farads.
- Assuming overhead-line intuition (`X0 >> X1`) always applies to bonded single-core cables.
- Treating a sheath-only lower-bound result as a final protection-study value.

## 7. Engineering Advice
Use this page as a front-end data-quality filter before parameters are fed into fault, stability, or load-flow studies. Cable results are engineering approximations and should be checked against manufacturer data, measured records, PSCAD/EMTP/OpenDSS-style matrix data, or other formal line-constants tools before commissioning decisions.
