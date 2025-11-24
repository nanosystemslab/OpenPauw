# OpenPauw Switching Board – Design Notes

This document describes the signal-level connections between the main components
shown in the KiCad schematic: the Adafruit Feather RP2040, four MAX328EPE+
analog switch ICs (U1–U4), and the external pads/signal labels present in the
design.

---

## 1. Power Rails

### **3.3 V Rail**
- Powers all MAX328EPE+ devices: pins **13 (V+)** and **15 (EN)**.
- Powers the Adafruit Feather RP2040 (via its onboard regulator circuitry).

### **GND**
- Common ground shared by:
  - Feather RP2040 (pins 3 and 4 shown)
  - All MAX328EPE+ devices (pins **14 (GND)**)

---

## 2. MAX328EPE+ Devices (U1–U4)

Each MAX328EPE+ has:
- **8 independent SPST analog switches:** S1–S8  
- **Digital address/control pins:** A0, A1, A2  
- **Enable pin:** EN  
- **Two supply rails:** V+ (3.3 V), V− (GND)

All four devices U1, U2, U3, U4 appear wired identically in the schematic except for their switched outputs.

### ### Pin Mapping (Common to U1–U4)

| Function | MAX328 Pin | Connected To |
|---------|-------------|--------------|
| S1–S8 Switches | Pins 5–12 | Routed toward labeled pads (PAD_A, PAD_B, PAD_C, PAD_D) |
| V+ | Pin 13 | 3.3 V Rail |
| GND | Pin 14 | GND |
| EN | Pin 3 | Digital control from Feather (GPIO TBD) |
| A0 | Pin 1 | Digital control from Feather (GPIO TBD) |
| A1 | Pin 2 | Digital control from Feather (GPIO TBD) |
| A2 | Pin 4 | Digital control from Feather (GPIO TBD) |

> Note: The screenshot does not show which GPIO lines control A0–A2–EN.  
> Fill those in once routing is visible.

---

## 3. External Pads / Measurement Nodes

The design includes multiple labeled nets:

### **Current Input Pads**
- `I_PLUS`
- `I_MINUS`

These run into the left side of the schematic. Their destination is not visible in
the screenshot, but they likely lead to switching or measurement circuits.

### **Voltage Input Pads**
- `V_PLUS`
- `V_MINUS`

Likewise fed into the left of the schematic.

### **Pulse Output Pads (Right Side)**
- `PAD_A`
- `PAD_B`
- `PAD_C`
- `PAD_D`

These appear to be outputs (or switched analog paths) from MAX328 banks.

Each MAX328 device likely corresponds roughly to:

| Device | Output Group |
|--------|--------------|
| U1 | PAD_A group |
| U2 | PAD_B group |
| U3 | PAD_C group |
| U4 | PAD_D group |

…but exact mapping depends on hidden net labels, to be confirmed once routing is inspected.

---

## 4. Adafruit Feather RP2040 (U5)

Relevant visible pins:

| Feather Pin | Label | Function |
|-------------|--------|----------|
| Pin 1 | RESET | Board reset |
| Pin 2 | 3.3V | System supply |
| Pin 3 | 3.3V | System supply |
| Pin 4 | GND | Ground |
| Pins 5–28 | GPIO | Used for MAX328 digital control, I²C, SPI, UART, etc. |

Visible routed GPIO lines from the screenshot (to be verified in layout):

- GPIO lines likely drive:
  - **EN** (enable) for each MAX328  
  - **A0/A1/A2** address pins for bank selection  
- Remaining GPIO may be used for measurement, communication, or enable logic.

### Visible GPIOs from schematic text:
- `AO/GPIO26`
- `A1/GPIO27`
- `A2/GPIO28`
- `A3/GPIO29`
- `D24/GPIO24`
- `D25/GPIO25`
- `D11/GPIO11`
- `D10/GPIO10`
- `D9/GPIO9`
- `D6/GPIO6`
- `D5/GPIO7?` (text cropped)
- `SCL/GPIO5`
- `SDA/GPIO4`

Assignments to MAX328 control pins should be finalized once routing is fully visible.

---

## 5. Summary of Intended Function

This board routes analog signals (current and voltage) from I+/I– and V+/V– into selectable output pads using four MAX328EPE+ analog switch ICs.  
The Feather RP2040 controls which path is active via digital addressing pins, enabling flexible switching matrices.

---

## 6. TODO (Complete Once Routing Is Visible)

- Confirm which GPIO pins from Feather connect to:
  - U1–U4 EN pins  
  - U1–U4 A0 pins  
  - U1–U4 A1 pins  
  - U1–U4 A2 pins  

- Verify the mapping of S1–S8 outputs to:
  - PAD_A  
  - PAD_B  
  - PAD_C  
  - PAD_D  

- Identify line routing between I+/I−, V+/V− and switch banks.

---
