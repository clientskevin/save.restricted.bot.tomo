#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
File: translator.py
Author: Maria Kevin
Created: 2025-11-17
Description: Brief description
"""

__author__ = "Maria Kevin"
__version__ = "0.1.0"


from googletrans import Translator


import asyncio


async def translate_fr_to_en(text: str) -> str:
    translator = Translator()
    for attempt in range(3):
        try:
            result = await translator.translate(text, dest="es")
            return result.text
        except Exception:
            if attempt == 2:
                raise
            await asyncio.sleep(2**attempt)

