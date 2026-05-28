"""Tests for resume template backend service."""
import pytest
from app.template_service import list_templates


class TestTemplateListing:
    def test_returns_ten_templates(self):
        """Verify exactly 10 templates are available."""
        templates = list_templates()
        assert len(templates) == 10

    def test_each_template_has_required_fields(self):
        """Verify each template has id, name, and thumbnail_url."""
        templates = list_templates()
        for t in templates:
            assert "id" in t
            assert "name" in t
            assert "thumbnail_url" in t
            assert isinstance(t["id"], str)
            assert isinstance(t["name"], str)
