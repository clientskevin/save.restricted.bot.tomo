#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
File: translator.py
Author: Maria Kevin
Created: 2025-11-17
Description: OpenAI-based translator that preserves HTML tags and special characters
"""

__author__ = "Maria Kevin"
__version__ = "0.2.0"

import asyncio

from openai import AsyncOpenAI

from bot.config import settings

client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)


async def translate(text: str, target_lang: str = "es") -> str:
    """
    Translate text to target language using OpenAI GPT-3.5 Turbo.
    Preserves HTML tags, special characters, and symbols.
    
    Args:
        text: Text to translate
        target_lang: Target language code (default: "es")
    
    Returns:
        Translated text with preserved formatting
    """
    prompt = f"""Translate the following text to "{target_lang}" language word-to-word.

IMPORTANT RULES:
- Do NOT translate HTML tags, keep them exactly as they are
- Do NOT translate or modify special characters, symbols, or weird letters
- ONLY translate the actual words/content
- Do NOT add any extra content, explanations, or formatting
- Return ONLY the translated text, nothing else

Text to translate to "{target_lang}":
Input: {text}

Ouput:
Translate and return only the input text in "{target_lang}" language word-to-word."""

    for attempt in range(3):
        try:
            response = await client.chat.completions.create(
                model="gpt-4.1",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            if attempt == 2:
                raise e
            await asyncio.sleep(2**attempt)
