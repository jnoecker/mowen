"""Shared fixtures for mowen tests."""

from __future__ import annotations

import pytest

from mowen.types import Document


@pytest.fixture
def sample_documents() -> list[Document]:
    """A small set of documents for testing."""
    return [
        Document(
            text="The quick brown fox jumps over the lazy dog. "
            "The fox is very quick and clever.",
            author="Author A",
            title="foxdoc",
        ),
        Document(
            text="A lazy dog sleeps in the sun all day long. "
            "The dog is extremely lazy and slow.",
            author="Author B",
            title="dogdoc",
        ),
        Document(
            text="Cats are independent creatures. "
            "The cat sat on the mat and watched birds.",
            author="Author A",
            title="catdoc",
        ),
    ]


@pytest.fixture
def unknown_document() -> Document:
    """An unknown document similar to Author A's style."""
    return Document(
        text="The quick fox ran across the field. "
        "The fox is nimble and quick on its feet.",
        title="mystery",
    )
