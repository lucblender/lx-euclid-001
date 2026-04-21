# EEPROM Structure Documentation

This document describes the EEPROM memory layout used by the LX-Euclid device. The structure is defined by the `create_memory_list()` method in `lxEuclidConfig.py`.

Latest version EEPROM version: v1.1.3.

## Memory Layout Table

| Address | Description of Content | EEPROM version |
|---------|------------------------|----------------|
| 0 | Memory mapping version major number | v1.1.0 |
| 1 | Memory mapping version minor number | v1.1.0 |
| 2 | Memory mapping version fix number | v1.1.0 |

### Euclidean Rhythms (Channels 0-3)

| Address | Description of Content | EEPROM version |
|---------|------------------------|----------------|
| 3 | Euclidean Rhythm 0 - Beats count | v1.1.0 |
| 4 | Euclidean Rhythm 0 - Pulses count | v1.1.0 |
| 5 | Euclidean Rhythm 0 - Offset value | v1.1.0 |
| 6 | Euclidean Rhythm 0 - Pulses probability (0-100) | v1.1.0 |
| 7 | Euclidean Rhythm 0 - Algorithm index | v1.1.0 |
| 8 | Euclidean Rhythm 0 - Prescaler index | v1.1.0 |
| 9 | Euclidean Rhythm 0 - Gate length in milliseconds | v1.1.0 |
| 10 | Euclidean Rhythm 0 - Randomize gate length flag | v1.1.0 |
| 11 | Euclidean Rhythm 0 - Burst division index | v1.1.0 |
| 12 | Euclidean Rhythm 1 - Beats count | v1.1.0 |
| 13 | Euclidean Rhythm 1 - Pulses count | v1.1.0 |
| 14 | Euclidean Rhythm 1 - Offset value | v1.1.0 |
| 15 | Euclidean Rhythm 1 - Pulses probability (0-100) | v1.1.0 |
| 16 | Euclidean Rhythm 1 - Algorithm index | v1.1.0 |
| 17 | Euclidean Rhythm 1 - Prescaler index | v1.1.0 |
| 18 | Euclidean Rhythm 1 - Gate length in milliseconds | v1.1.0 |
| 19 | Euclidean Rhythm 1 - Randomize gate length flag | v1.1.0 |
| 20 | Euclidean Rhythm 1 - Burst division index | v1.1.0 |
| 21 | Euclidean Rhythm 2 - Beats count | v1.1.0 |
| 22 | Euclidean Rhythm 2 - Pulses count | v1.1.0 |
| 23 | Euclidean Rhythm 2 - Offset value | v1.1.0 |
| 24 | Euclidean Rhythm 2 - Pulses probability (0-100) | v1.1.0 |
| 25 | Euclidean Rhythm 2 - Algorithm index | v1.1.0 |
| 26 | Euclidean Rhythm 2 - Prescaler index | v1.1.0 |
| 27 | Euclidean Rhythm 2 - Gate length in milliseconds | v1.1.0 |
| 28 | Euclidean Rhythm 2 - Randomize gate length flag | v1.1.0 |
| 29 | Euclidean Rhythm 2 - Burst division index | v1.1.0 |
| 30 | Euclidean Rhythm 3 - Beats count | v1.1.0 |
| 31 | Euclidean Rhythm 3 - Pulses count | v1.1.0 |
| 32 | Euclidean Rhythm 3 - Offset value | v1.1.0 |
| 33 | Euclidean Rhythm 3 - Pulses probability (0-100) | v1.1.0 |
| 34 | Euclidean Rhythm 3 - Algorithm index | v1.1.0 |
| 35 | Euclidean Rhythm 3 - Prescaler index | v1.1.0 |
| 36 | Euclidean Rhythm 3 - Gate length in milliseconds | v1.1.0 |
| 37 | Euclidean Rhythm 3 - Randomize gate length flag | v1.1.0 |
| 38 | Euclidean Rhythm 3 - Burst division index | v1.1.0 |

### Presets (8 Presets × 4 Rhythms each)

| Address | Description of Content | EEPROM version |
|---------|------------------------|----------------|
| 39 | Preset 0, Rhythm 0 - Beats count | v1.1.0 |
| 40 | Preset 0, Rhythm 0 - Pulses count | v1.1.0 |
| 41 | Preset 0, Rhythm 0 - Offset value | v1.1.0 |
| 42 | Preset 0, Rhythm 0 - Pulses probability | v1.1.0 |
| 43 | Preset 0, Rhythm 0 - Algorithm index | v1.1.0 |
| 44 | Preset 0, Rhythm 0 - Prescaler index | v1.1.0 |
| 45 | Preset 0, Rhythm 0 - Gate length in ms | v1.1.0 |
| 46 | Preset 0, Rhythm 0 - Randomize gate length | v1.1.0 |
| 47 | Preset 0, Rhythm 0 - Burst division index | v1.1.0 |
| 48 | Preset 0, Rhythm 1 - Beats count | v1.1.0 |
| 49 | Preset 0, Rhythm 1 - Pulses count | v1.1.0 |
| 50 | Preset 0, Rhythm 1 - Offset value | v1.1.0 |
| 51 | Preset 0, Rhythm 1 - Pulses probability | v1.1.0 |
| 52 | Preset 0, Rhythm 1 - Algorithm index | v1.1.0 |
| 53 | Preset 0, Rhythm 1 - Prescaler index | v1.1.0 |
| 54 | Preset 0, Rhythm 1 - Gate length in ms | v1.1.0 |
| 55 | Preset 0, Rhythm 1 - Randomize gate length | v1.1.0 |
| 56 | Preset 0, Rhythm 1 - Burst division index | v1.1.0 |
| 57 | Preset 0, Rhythm 2 - Beats count | v1.1.0 |
| 58 | Preset 0, Rhythm 2 - Pulses count | v1.1.0 |
| 59 | Preset 0, Rhythm 2 - Offset value | v1.1.0 |
| 60 | Preset 0, Rhythm 2 - Pulses probability | v1.1.0 |
| 61 | Preset 0, Rhythm 2 - Algorithm index | v1.1.0 |
| 62 | Preset 0, Rhythm 2 - Prescaler index | v1.1.0 |
| 63 | Preset 0, Rhythm 2 - Gate length in ms | v1.1.0 |
| 64 | Preset 0, Rhythm 2 - Randomize gate length | v1.1.0 |
| 65 | Preset 0, Rhythm 2 - Burst division index | v1.1.0 |
| 66 | Preset 0, Rhythm 3 - Beats count | v1.1.0 |
| 67 | Preset 0, Rhythm 3 - Pulses count | v1.1.0 |
| 68 | Preset 0, Rhythm 3 - Offset value | v1.1.0 |
| 69 | Preset 0, Rhythm 3 - Pulses probability | v1.1.0 |
| 70 | Preset 0, Rhythm 3 - Algorithm index | v1.1.0 |
| 71 | Preset 0, Rhythm 3 - Prescaler index | v1.1.0 |
| 72 | Preset 0, Rhythm 3 - Gate length in ms | v1.1.0 |
| 73 | Preset 0, Rhythm 3 - Randomize gate length | v1.1.0 |
| 74 | Preset 0, Rhythm 3 - Burst division index | v1.1.0 |

*Note: Presets 1-7 follow the same pattern, with addresses 75-326*

### Global Settings

| Address | Description of Content | EEPROM version |
|---------|------------------------|----------------|
| 327 | Inner rotate action | v1.1.0 |
| 328 | Inner action rhythm | v1.1.0 |
| 329 | Outer rotate action | v1.1.0 |
| 330 | Outer action rhythm | v1.1.0 |
| 331 | Touch sensitivity | v1.1.0 |
| 332 | Clock mode | v1.1.0 |

### CV Configuration (4 Channels × 9 Actions each)

| Address | Description of Content | EEPROM version |
|---------|------------------------|----------------|
| 333 | CV Channel 0, Action 0 - Channel assignment | v1.1.0 |
| 334 | CV Channel 0, Action 1 - Channel assignment | v1.1.0 |
| 335 | CV Channel 0, Action 2 - Channel assignment | v1.1.0 |
| 336 | CV Channel 0, Action 3 - Channel assignment | v1.1.0 |
| 337 | CV Channel 0, Action 4 - Channel assignment | v1.1.0 |
| 338 | CV Channel 0, Action 5 - Channel assignment | v1.1.0 |
| 339 | CV Channel 0, Action 6 - Channel assignment | v1.1.0 |
| 340 | CV Channel 0, Action 7 - Channel assignment | v1.1.0 |
| 341 | CV Channel 0, Action 8 - Channel assignment | v1.1.0 |

*Note: CV Channels 1-3 follow the same pattern, with addresses 342-368*

### Timing and Display Settings

| Address | Description of Content | EEPROM version |
|---------|------------------------|----------------|
| 369 | Tap tempo delay LSB (lower 8 bits) | v1.1.0 |
| 370 | Tap tempo delay MSB (upper 8 bits) | v1.1.0 |
| 371 | Display flip setting | v1.1.0 |
| 372 | Preset recall mode | v1.1.0 |

### Custom Rhythms (4 Channels)

| Address | Description of Content | EEPROM version |
|---------|------------------------|----------------|
| 373 | Euclidean Rhythm 0 - Custom rhythm BYTE_0 | v1.1.1 |
| 374 | Euclidean Rhythm 0 - Custom rhythm BYTE_1 | v1.1.1 |
| 375 | Euclidean Rhythm 0 - Custom rhythm BYTE_2 | v1.1.1 |
| 376 | Euclidean Rhythm 0 - Custom rhythm BYTE_3 | v1.1.1 |
| 377 | Euclidean Rhythm 1 - Custom rhythm BYTE_0 | v1.1.1 |
| 378 | Euclidean Rhythm 1 - Custom rhythm BYTE_1 | v1.1.1 |
| 379 | Euclidean Rhythm 1 - Custom rhythm BYTE_2 | v1.1.1 |
| 380 | Euclidean Rhythm 1 - Custom rhythm BYTE_3 | v1.1.1 |
| 381 | Euclidean Rhythm 2 - Custom rhythm BYTE_0 | v1.1.1 |
| 382 | Euclidean Rhythm 2 - Custom rhythm BYTE_1 | v1.1.1 |
| 383 | Euclidean Rhythm 2 - Custom rhythm BYTE_2 | v1.1.1 |
| 384 | Euclidean Rhythm 2 - Custom rhythm BYTE_3 | v1.1.1 |
| 385 | Euclidean Rhythm 3 - Custom rhythm BYTE_0 | v1.1.1 |
| 386 | Euclidean Rhythm 3 - Custom rhythm BYTE_1 | v1.1.1 |
| 387 | Euclidean Rhythm 3 - Custom rhythm BYTE_2 | v1.1.1 |
| 388 | Euclidean Rhythm 3 - Custom rhythm BYTE_3 | v1.1.1 |

### Algorithm Custom Flags (4 Channels)

| Address | Description of Content | EEPROM version |
|---------|------------------------|----------------|
| 389 | Euclidean Rhythm 0 - Algorithm custom flag | v1.1.3 |
| 390 | Euclidean Rhythm 1 - Algorithm custom flag | v1.1.3 |
| 391 | Euclidean Rhythm 2 - Algorithm custom flag | v1.1.3 |
| 392 | Euclidean Rhythm 3 - Algorithm custom flag | v1.1.3 |

### Preset Custom Rhythms (8 Presets × 4 Rhythms each)

| Address | Description of Content | EEPROM version |
|---------|------------------------|----------------|
| 393 | Preset 0, Rhythm 0 - Custom rhythm BYTE_0 | v1.1.1 |
| 394 | Preset 0, Rhythm 0 - Custom rhythm BYTE_1 | v1.1.1 |
| 395 | Preset 0, Rhythm 0 - Custom rhythm BYTE_2 | v1.1.1 |
| 396 | Preset 0, Rhythm 0 - Custom rhythm BYTE_3 | v1.1.1 |
| 397 | Preset 0, Rhythm 1 - Custom rhythm BYTE_0 | v1.1.1 |
| 398 | Preset 0, Rhythm 1 - Custom rhythm BYTE_1 | v1.1.1 |
| 399 | Preset 0, Rhythm 1 - Custom rhythm BYTE_2 | v1.1.1 |
| 400 | Preset 0, Rhythm 1 - Custom rhythm BYTE_3 | v1.1.1 |
| 401 | Preset 0, Rhythm 2 - Custom rhythm BYTE_0 | v1.1.1 |
| 402 | Preset 0, Rhythm 2 - Custom rhythm BYTE_1 | v1.1.1 |
| 403 | Preset 0, Rhythm 2 - Custom rhythm BYTE_2 | v1.1.1 |
| 404 | Preset 0, Rhythm 2 - Custom rhythm BYTE_3 | v1.1.1 |
| 405 | Preset 0, Rhythm 3 - Custom rhythm BYTE_0 | v1.1.1 |
| 406 | Preset 0, Rhythm 3 - Custom rhythm BYTE_1 | v1.1.1 |
| 407 | Preset 0, Rhythm 3 - Custom rhythm BYTE_2 | v1.1.1 |
| 408 | Preset 0, Rhythm 3 - Custom rhythm BYTE_3 | v1.1.1 |

*Note: Presets 1-7 follow the same pattern, with addresses 409-520*

### Preset Algorithm Custom Flags (8 Presets × 4 Rhythms each)

| Address | Description of Content | EEPROM version |
|---------|------------------------|----------------|
| 521 | Preset 0, Rhythm 0 - Algorithm custom flag | v1.1.3 |
| 522 | Preset 0, Rhythm 1 - Algorithm custom flag | v1.1.3 |
| 523 | Preset 0, Rhythm 2 - Algorithm custom flag | v1.1.3 |
| 524 | Preset 0, Rhythm 3 - Algorithm custom flag | v1.1.3 |

*Note: Presets 1-7 follow the same pattern, with addresses 525-552*

### Gate Length Percentage Management (4 Channels)

| Address | Description of Content | EEPROM version |
|---------|------------------------|----------------|
| 553 | Euclidean Rhythm 0 - Gate length mode (ms/percent) | v1.1.2 |
| 554 | Euclidean Rhythm 0 - Gate length percentage | v1.1.2 |
| 555 | Euclidean Rhythm 1 - Gate length mode (ms/percent) | v1.1.2 |
| 556 | Euclidean Rhythm 1 - Gate length percentage | v1.1.2 |
| 557 | Euclidean Rhythm 2 - Gate length mode (ms/percent) | v1.1.2 |
| 558 | Euclidean Rhythm 2 - Gate length percentage | v1.1.2 |
| 559 | Euclidean Rhythm 3 - Gate length mode (ms/percent) | v1.1.2 |
| 560 | Euclidean Rhythm 3 - Gate length percentage | v1.1.2 |

### Preset Gate Length Percentage Management (8 Presets × 4 Rhythms each)

| Address | Description of Content | EEPROM version |
|---------|------------------------|----------------|
| 561 | Preset 0, Rhythm 0 - Gate length mode (ms/percent) | v1.1.2 |
| 562 | Preset 0, Rhythm 0 - Gate length percentage | v1.1.2 |
| 563 | Preset 0, Rhythm 1 - Gate length mode (ms/percent) | v1.1.2 |
| 564 | Preset 0, Rhythm 1 - Gate length percentage | v1.1.2 |
| 565 | Preset 0, Rhythm 2 - Gate length mode (ms/percent) | v1.1.2 |
| 566 | Preset 0, Rhythm 2 - Gate length percentage | v1.1.2 |
| 567 | Preset 0, Rhythm 3 - Gate length mode (ms/percent) | v1.1.2 |
| 568 | Preset 0, Rhythm 3 - Gate length percentage | v1.1.2 |

*Note: Presets 1-7 follow the same pattern, with addresses 569-624*

## Total EEPROM Size

**625 bytes** total are used for configuration storage. This size is defined in LxEuclidConstant.MEMORY_LIST_SIZE.
