# EEPROM Structure Documentation

This document describes the EEPROM memory layout used by the LX-Euclid device. The structure is defined by the `create_memory_list()` method in `lxEuclidConfig.py`.

## Memory Layout Table

| Address | Description of Content |
|---------|------------------------|
| 0 | Memory mapping version major number |
| 1 | Memory mapping version minor number |
| 2 | Memory mapping version fix number |

### Euclidean Rhythms (Channels 0-3)

| Address | Description of Content |
|---------|------------------------|
| 3 | Euclidean Rhythm 0 - Beats count |
| 4 | Euclidean Rhythm 0 - Pulses count |
| 5 | Euclidean Rhythm 0 - Offset value |
| 6 | Euclidean Rhythm 0 - Pulses probability (0-100) |
| 7 | Euclidean Rhythm 0 - Algorithm index |
| 8 | Euclidean Rhythm 0 - Prescaler index |
| 9 | Euclidean Rhythm 0 - Gate length in milliseconds |
| 10 | Euclidean Rhythm 0 - Randomize gate length flag |
| 11 | Euclidean Rhythm 0 - Burst division index |
| 12 | Euclidean Rhythm 1 - Beats count |
| 13 | Euclidean Rhythm 1 - Pulses count |
| 14 | Euclidean Rhythm 1 - Offset value |
| 15 | Euclidean Rhythm 1 - Pulses probability (0-100) |
| 16 | Euclidean Rhythm 1 - Algorithm index |
| 17 | Euclidean Rhythm 1 - Prescaler index |
| 18 | Euclidean Rhythm 1 - Gate length in milliseconds |
| 19 | Euclidean Rhythm 1 - Randomize gate length flag |
| 20 | Euclidean Rhythm 1 - Burst division index |
| 21 | Euclidean Rhythm 2 - Beats count |
| 22 | Euclidean Rhythm 2 - Pulses count |
| 23 | Euclidean Rhythm 2 - Offset value |
| 24 | Euclidean Rhythm 2 - Pulses probability (0-100) |
| 25 | Euclidean Rhythm 2 - Algorithm index |
| 26 | Euclidean Rhythm 2 - Prescaler index |
| 27 | Euclidean Rhythm 2 - Gate length in milliseconds |
| 28 | Euclidean Rhythm 2 - Randomize gate length flag |
| 29 | Euclidean Rhythm 2 - Burst division index |
| 30 | Euclidean Rhythm 3 - Beats count |
| 31 | Euclidean Rhythm 3 - Pulses count |
| 32 | Euclidean Rhythm 3 - Offset value |
| 33 | Euclidean Rhythm 3 - Pulses probability (0-100) |
| 34 | Euclidean Rhythm 3 - Algorithm index |
| 35 | Euclidean Rhythm 3 - Prescaler index |
| 36 | Euclidean Rhythm 3 - Gate length in milliseconds |
| 37 | Euclidean Rhythm 3 - Randomize gate length flag |
| 38 | Euclidean Rhythm 3 - Burst division index |

### Presets (8 Presets × 4 Rhythms each)

| Address | Description of Content |
|---------|------------------------|
| 39 | Preset 0, Rhythm 0 - Beats count |
| 40 | Preset 0, Rhythm 0 - Pulses count |
| 41 | Preset 0, Rhythm 0 - Offset value |
| 42 | Preset 0, Rhythm 0 - Pulses probability |
| 43 | Preset 0, Rhythm 0 - Algorithm index |
| 44 | Preset 0, Rhythm 0 - Prescaler index |
| 45 | Preset 0, Rhythm 0 - Gate length in ms |
| 46 | Preset 0, Rhythm 0 - Randomize gate length |
| 47 | Preset 0, Rhythm 0 - Burst division index |
| 48 | Preset 0, Rhythm 1 - Beats count |
| 49 | Preset 0, Rhythm 1 - Pulses count |
| 50 | Preset 0, Rhythm 1 - Offset value |
| 51 | Preset 0, Rhythm 1 - Pulses probability |
| 52 | Preset 0, Rhythm 1 - Algorithm index |
| 53 | Preset 0, Rhythm 1 - Prescaler index |
| 54 | Preset 0, Rhythm 1 - Gate length in ms |
| 55 | Preset 0, Rhythm 1 - Randomize gate length |
| 56 | Preset 0, Rhythm 1 - Burst division index |
| 57 | Preset 0, Rhythm 2 - Beats count |
| 58 | Preset 0, Rhythm 2 - Pulses count |
| 59 | Preset 0, Rhythm 2 - Offset value |
| 60 | Preset 0, Rhythm 2 - Pulses probability |
| 61 | Preset 0, Rhythm 2 - Algorithm index |
| 62 | Preset 0, Rhythm 2 - Prescaler index |
| 63 | Preset 0, Rhythm 2 - Gate length in ms |
| 64 | Preset 0, Rhythm 2 - Randomize gate length |
| 65 | Preset 0, Rhythm 2 - Burst division index |
| 66 | Preset 0, Rhythm 3 - Beats count |
| 67 | Preset 0, Rhythm 3 - Pulses count |
| 68 | Preset 0, Rhythm 3 - Offset value |
| 69 | Preset 0, Rhythm 3 - Pulses probability |
| 70 | Preset 0, Rhythm 3 - Algorithm index |
| 71 | Preset 0, Rhythm 3 - Prescaler index |
| 72 | Preset 0, Rhythm 3 - Gate length in ms |
| 73 | Preset 0, Rhythm 3 - Randomize gate length |
| 74 | Preset 0, Rhythm 3 - Burst division index |

*Note: Presets 1-7 follow the same pattern, with addresses 75-326*

### Global Settings

| Address | Description of Content |
|---------|------------------------|
| 327 | Inner rotate action |
| 328 | Inner action rhythm |
| 329 | Outer rotate action |
| 330 | Outer action rhythm |
| 331 | Touch sensitivity |
| 332 | Clock mode |

### CV Configuration (4 Channels × 9 Actions each)

| Address | Description of Content |
|---------|------------------------|
| 333 | CV Channel 0, Action 0 - Channel assignment |
| 334 | CV Channel 0, Action 1 - Channel assignment |
| 335 | CV Channel 0, Action 2 - Channel assignment |
| 336 | CV Channel 0, Action 3 - Channel assignment |
| 337 | CV Channel 0, Action 4 - Channel assignment |
| 338 | CV Channel 0, Action 5 - Channel assignment |
| 339 | CV Channel 0, Action 6 - Channel assignment |
| 340 | CV Channel 0, Action 7 - Channel assignment |
| 341 | CV Channel 0, Action 8 - Channel assignment |

*Note: CV Channels 1-3 follow the same pattern, with addresses 342-368*

### Timing and Display Settings

| Address | Description of Content |
|---------|------------------------|
| 369 | Tap tempo delay LSB (lower 8 bits) |
| 370 | Tap tempo delay MSB (upper 8 bits) |
| 371 | Display flip setting |
| 372 | Preset recall mode |

### Custom Rhythms (4 Channels)

| Address | Description of Content |
|---------|------------------------|
| 373 | Euclidean Rhythm 0 - Custom rhythm LSB |
| 374 | Euclidean Rhythm 0 - Custom rhythm MSB |
| 375 | Euclidean Rhythm 1 - Custom rhythm LSB |
| 376 | Euclidean Rhythm 1 - Custom rhythm MSB |
| 377 | Euclidean Rhythm 2 - Custom rhythm LSB |
| 378 | Euclidean Rhythm 2 - Custom rhythm MSB |
| 379 | Euclidean Rhythm 3 - Custom rhythm LSB |
| 380 | Euclidean Rhythm 3 - Custom rhythm MSB |

### Preset Custom Rhythms (8 Presets × 4 Rhythms each)

| Address | Description of Content |
|---------|------------------------|
| 381 | Preset 0, Rhythm 0 - Custom rhythm LSB |
| 382 | Preset 0, Rhythm 0 - Custom rhythm MSB |
| 383 | Preset 0, Rhythm 1 - Custom rhythm LSB |
| 384 | Preset 0, Rhythm 1 - Custom rhythm MSB |
| 385 | Preset 0, Rhythm 2 - Custom rhythm LSB |
| 386 | Preset 0, Rhythm 2 - Custom rhythm MSB |
| 387 | Preset 0, Rhythm 3 - Custom rhythm LSB |
| 388 | Preset 0, Rhythm 3 - Custom rhythm MSB |

*Note: Presets 1-7 follow the same pattern, with addresses 389-444*

## Total EEPROM Size

**445 bytes** total are used for configuration storage.
