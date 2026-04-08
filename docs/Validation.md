# OpenPauw System Validation

Procedures for verifying that the OpenPauw Van der Pauw measurement system is producing accurate, reliable results.

## 1. Switch Matrix Integrity

Confirm that the MAX328 analog switches are routing signals correctly.

```bash
openpauw swtest
openpauw cfgtest
```

Both should report PASS. If either fails, check I2C connections to the MCP23017 and power to the MAX328 ICs (+15V boost converter output).

## 2. Known Sample Measurement

Measure a sample with a known sheet resistance and compare to the expected value.

### Option A: NIST-Traceable Standard

If available, use a NIST-traceable thin film resistivity standard. These typically come with a certified Rs value and uncertainty. Your measured value should fall within the certified uncertainty.

### Option B: Bulk Metal Foil

Use a piece of metal foil with known bulk resistivity and measure its thickness with a micrometer.

| Material | Bulk Resistivity (ohm-cm) |
|----------|--------------------------|
| Copper   | 1.68e-6                  |
| Aluminum | 2.65e-6                  |
| Nickel   | 6.99e-6                  |

Expected sheet resistance:

```
Rs = rho / t
```

where `rho` is bulk resistivity and `t` is thickness in cm.

Example: 25 µm copper foil → Rs = 1.68e-6 / 2.5e-3 = 6.72e-4 ohm/sq

### Pass Criteria

Measured Rs within 2% of the known value.

## 3. Reciprocity Check

The Van der Pauw method relies on reciprocity — swapping current and voltage terminals should yield the same resistance. The four configurations form two forward/reverse pairs:

- **Horizontal pair:** CFG 1 and CFG 2
- **Vertical pair:** CFG 3 and CFG 4

Run a measurement and check:

```bash
openpauw measure --dmm-ip <IP> --current 100e-6
```

Verify:

```
|V1| ≈ |V2|    (horizontal pair)
|V3| ≈ |V4|    (vertical pair)
```

### Pass Criteria

Each forward/reverse pair should agree within 2%. Larger discrepancies indicate:

- Poor contact quality (dirty or misaligned probes)
- Switch leakage or routing error
- Sample non-uniformity near the contacts

## 4. Repeatability

Run repeated measurements on the same sample without disturbing the contacts.

```bash
# Run 10 measurements, saving all to CSV
for i in $(seq 1 10); do
    openpauw measure --dmm-ip <IP> --current 100e-6 --output repeatability.csv
done
```

Compute the mean and standard deviation of the sheet resistance column from the CSV.

### Pass Criteria

Coefficient of variation (CV = standard deviation / mean) should be < 1%.

If CV exceeds 1%, try:

- Increasing `--nplc` (e.g. 15) for better noise rejection
- Increasing `--settle` time (e.g. 0.5 s)
- Checking probe contact pressure and stability

## 5. Current Linearity

Sheet resistance should be independent of the applied current for an ohmic sample. Measure at several current levels:

```bash
openpauw measure --dmm-ip <IP> --current 10e-6  --output linearity.csv
openpauw measure --dmm-ip <IP> --current 50e-6  --output linearity.csv
openpauw measure --dmm-ip <IP> --current 100e-6 --output linearity.csv
openpauw measure --dmm-ip <IP> --current 500e-6 --output linearity.csv
```

Plot Rs vs. current. The result should be a flat line.

### Pass Criteria

Rs should not vary by more than 2% across the current range.

Deviations indicate:

- **Rs increases with current** — Joule heating in the sample
- **Rs decreases with current** — non-ohmic contacts (Schottky barrier, oxide layer)
- **Rs unstable at low current** — voltage signal too small relative to DMM noise floor; increase current or NPLC

## Validation Summary

| Test | What It Checks | Pass Criteria |
|------|---------------|---------------|
| Switch matrix (swtest/cfgtest) | Hardware routing | PASS |
| Known sample | Absolute accuracy | Within 2% of known Rs |
| Reciprocity | Contact and switch quality | Forward/reverse pairs within 2% |
| Repeatability | Measurement noise | CV < 1% over 10 runs |
| Current linearity | Ohmic behavior, heating | Rs within 2% across currents |

## Recording Results

Keep a validation log with date, sample ID, firmware version, and results for each test. Re-validate after any hardware changes (new probe card, board revision, firmware update).
