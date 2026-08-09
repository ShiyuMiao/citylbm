#pragma once

#define D3Q19
#define SRT
#define FP16S
#define EQUILIBRIUM_BOUNDARIES


#define TYPE_S 0b00000001
#define TYPE_E 0b00000010
#define TYPE_T 0b00000100
#define TYPE_F 0b00001000
#define TYPE_I 0b00010000
#define TYPE_G 0b00100000
#define TYPE_X 0b01000000
#define TYPE_Y 0b10000000

#if defined(FP16S) || defined(FP16C)
#define fpxx ushort
#else
#define fpxx float
#endif
