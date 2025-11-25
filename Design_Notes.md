# OpenPauw Switching Board – Pin Mapping & Power Requirements

This document specifies the exact connections between the Adafruit Feather RP2040,
the MAX328EPE+ analog switch ICs (U1–U4), and the 15 V boost supply so that PCB
layout and routing can be completed without opening the schematic.

The goal is to implement a 4-terminal switching matrix suitable for
Van der Pauw–style measurements:

- Terminals: **I+**, **I−**, **V+**, **V−**
- Each terminal is routed through a dedicated MAX328EPE+ device.
- The Feather RP2040 controls which of 8 switch legs (S1–S8) is connected to
  each terminal via the device’s common node **D**.

---

## 1. Power Domains & References

### 1.1 Rails

| Rail Name | Nominal Voltage | Source                           | Used By                                   | Notes |
|----------|-----------------|-----------------------------------|-------------------------------------------|-------|
| 3V3      | 3.3 V           | Feather on-board regulator       | Feather digital, MAX328 logic pins (EN, A0–A2) | Decouple locally near Feather and each MAX328. |
| VUSB     | 5 V             | Feather USB connector (VUSB pin) | Input to 15 V boost (LMR62421)            | Only present when USB is powered. |
| +15V     | 15 V            | LMR62421 boost from VUSB         | MAX328EPE+ V+ pins, analog domain as needed | See Section 6 for requirements. |
| GND      | 0 V             | Common board ground              | Feather, MAX328EPE+, LMR62421, all I/O    | Single solid ground plane recommended. |

### 1.2 MAX328EPE+ Supply Reference

For **all** MAX328EPE+ devices (U1–U4):

- **V+** (pin 13) → **+15V rail**
- **V−** (pin 3) → **GND**

> In this design the MAX328EPE+ is used as a **unipolar 0–15 V** analog switch,
> so **V− is tied directly to board ground**.

---

## 2. Adafruit Feather RP2040 – Power & Reference Pins

| Function      | Feather Pin Label | Notes                                            |
|--------------|-------------------|--------------------------------------------------|
| 3.3 V Rail   | 3V / 3V3          | Feeds digital 3.3 V domain and MAX328 logic pins |
| GND          | GND               | Common reference for logic and MAX328 V−        |
| VUSB (Boost) | VBUS / USB5V      | Input to LMR62421 boost to create +15 V         |

(Use the exact KiCad symbol pin names for 3V3, GND, and VUSB as placed in the schematic.)

---

## 3. MAX328EPE+ Digital Control – Feather GPIO Mapping

Each MAX328EPE+ has three address inputs (A0–A2) and an enable input (EN).

- **A0, A1, A2 are shared (bussed) between U1–U4** so that the same 3-bit code
  selects the active switch leg index (S1–S8) on all four devices simultaneously.
- **EN is unique per device** so that the Feather can select which terminal
  (I+, I−, V+, V−) is active for that leg.

### 3.1 Address Bus (Shared A0–A2 for U1–U4)

| Signal Role | Feather Label | Feather GPIO # | Connected Devices | IC Pin Name | IC Pin # (U1–U4) | Notes |
|-------------|---------------|----------------|-------------------|------------|------------------|-------|
| Address A0  | D10           | GPIO10         | U1, U2, U3, U4    | A0         | Pin 1           | Shared 3-bit LSB |
| Address A1  | D11           | GPIO11         | U1, U2, U3, U4    | A1         | Pin 16          | Shared 3-bit mid |
| Address A2  | D12           | GPIO12         | U1, U2, U3, U4    | A2         | Pin 15          | Shared 3-bit MSB |

> When `[A2 A1 A0]` is driven with a value 0–7, all four MAX328 devices
> simultaneously select S1–S8 corresponding to that address. Their individual
> EN pins determine which terminals are actually connected.

### 3.2 Individual Enables (EN) per MAX328

| Function / Terminal | Feather Label | Feather GPIO # | IC RefDes | IC Pin Name | IC Pin # |
|---------------------|---------------|----------------|-----------|-------------|---------:|
| EN for I+ device    | D9            | GPIO9          | U1        | EN          | 2        |
| EN for I− device    | D6            | GPIO6          | U2        | EN          | 2        |
| EN for V+ device    | D5            | GPIO5          | U3        | EN          | 2        |
| EN for V− device    | D4            | GPIO4          | U4        | EN          | 2        |

Suggested firmware pattern:

- Drive `[A2 A1 A0]` for desired leg index 0–7.
- Assert exactly **one** EN line high (U1–U4) at a time to connect that
  terminal to the selected Sx node.
- De-assert all EN lines when changing addresses to avoid transient shorts.

---

## 4. Analog Paths – Terminals & MAX328 Connections

Each MAX328EPE+ is used as an **8-throw analog switch** connecting its **D** pin
to one of the S1–S8 pins according to the address and EN.

### 4.1 Terminal Assignment per MAX328 Device

| Terminal Role | Board Net Name | IC RefDes | IC Pin Name | IC Pin # | Notes |
|---------------|----------------|-----------|-------------|---------:|-------|
| Current +     | I_PLUS         | U1        | D           | 8        | U1 handles all paths for I+ terminal. |
| Current −     | I_MINUS        | U2        | D           | 8        | U2 handles all paths for I− terminal. |
| Voltage +     | V_PLUS         | U3        | D           | 8        | U3 handles all paths for V+ terminal. |
| Voltage −     | V_MINUS        | U4        | D           | 8        | U4 handles all paths for V− terminal. |

### 4.2 S-Pin Routing (Measurement Nodes)

Each device has eight switch legs S1–S8. For layout, route them as
corresponding “measurement pads” or connection points (PAD\_1…PAD\_8, or
per-sample pads):

| Device | Terminal | S-Pin | Net (example)   | Notes                          |
|--------|----------|-------|-----------------|--------------------------------|
| U1     | I+       | S1–S8 | PAD\_A1–PAD\_A8 | Configure names to match PCB.  |
| U2     | I−       | S1–S8 | PAD\_B1–PAD\_B8 |                                |
| U3     | V+       | S1–S8 | PAD\_C1–PAD\_C8 |                                |
| U4     | V−       | S1–S8 | PAD\_D1–PAD\_D8 |                                |

> Exact pad names are up to the PCB designer; the key requirement is that for a
> given address value, **all four devices connect the same “index” leg (S1…S8)
> to I+, I−, V+, V− respectively.** This forms one complete 4-terminal contact
> set suitable for a Van der Pauw measurement.

---

## 5. MAX328EPE+ Power Pins & Decoupling

For **each** of U1–U4:

| Pin Name | Pin # | Net  | Notes |
|----------|-------|------|-------|
| V+       | 13    | +15V | Decouple with 100 nF ceramic placed close to pin. |
| V−       | 3     | GND  | Tie directly to ground plane.                     |
| GND (symbol) | 14 | GND | Analog ground reference.                          |

Place additional bulk capacitance (e.g., 4.7 µF–10 µF) on the +15 V rail near the
cluster of MAX328 devices.

---

## 6. 15 V Boost Converter (LMR62421) Requirements

The +15 V rail is generated from the Feather’s **VUSB (5 V)** using the
**LMR62421** boost regulator in SOT-23-5, following the datasheet’s typical
application circuit.

### 6.1 Functional Connections

Using the TI reference design:

- **VIN:** VUSB (5 V from Feather USB input)
- **SW (switch node):**  
  - Connect to inductor **L1**, then to diode **D1**, then to VOUT node.
- **FB (feedback):**  
  - Connect to VOUT via resistor divider **R1/R2**.
- **GND:** Common ground (same as board GND and MAX328 V−).
- **SHDN / EN (if present on package variant):**  
  - Tie high to VIN for always-on, or route to a Feather GPIO for software control.

### 6.2 Output Voltage Setting

Target: **VOUT = 15 V**

- Choose **R1 / R2** per the LMR62421 datasheet equation:  

  \[
  V_{OUT} = V_{REF}\left(1 + \frac{R1}{R2}\right)
  \]

  where \(V_{REF}\) is the feedback reference voltage from the datasheet.

- Example (to be confirmed from datasheet):
  - R2 ≈ 10 kΩ  
  - R1 chosen to give ≈15 V (calculate exactly when selecting parts).

### 6.3 Component & Layout Notes

- **L1:** Choose inductance and current rating per TI design tables for
  5 V→15 V operation and expected load (all MAX328 devices plus any external load).
- **D1:** Fast Schottky diode rated for at least:
  - Reverse voltage ≥ 20 V
  - Forward current above maximum +15 V rail current.
- **C2, C3 (output caps):** Use low-ESR ceramics totaling several µF at 25 V+
  rating; place close to diode and LMR62421.
- **C1 (input cap):** 4.7–10 µF ceramic from VIN to GND, close to the IC.
- Route the boost loop (VIN–L1–D1–VOUT–GND) as tight as possible to minimize EMI.
- The **+15 V net** should primarily feed:
  - V+ pins of U1–U4
  - Any optional +15 V test points or measurement nodes
  - Avoid running +15 V near sensitive digital signals unless well-shielded.

---

## 7. Summary of Key Design Rules

1. **V− of all MAX328EPE+ devices is tied to GND**, giving a unipolar 0–15 V
   analog range.
2. **+15 V rail** is generated from **VUSB (5 V)** using an LMR62421 boost,
   and feeds only the MAX328 V+ pins and any explicit +15 V pads.
3. **Address bus A0–A2 is shared** across U1–U4; each device gets a **unique EN**
   line from the Feather.
4. **D pins**:
   - U1.D → I\_PLUS  
   - U2.D → I\_MINUS  
   - U3.D → V\_PLUS  
   - U4.D → V\_MINUS  
5. For a given address code, S1–S8 of U1–U4 must be routed so that the
   corresponding index forms one complete 4-terminal contact set for
   Van der Pauw measurements.

This document should contain everything a PCB/layout engineer needs to route the
board correctly without re-opening the schematic.
