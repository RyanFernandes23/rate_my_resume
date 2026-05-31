"""Tests for resume template backend service."""
import pytest
from app.template_service import list_templates


class TestTemplateListing:
    def test_returns_sixteen_templates(self):
        """Verify exactly 16 templates are available."""
        templates = list_templates()
        assert len(templates) == 16

    def test_jake_template_exists(self):
        """Verify the 'jake' template is registered."""
        templates = list_templates()
        jake = next((t for t in templates if t["id"] == "jake"), None)
        assert jake is not None
        assert jake["name"] == "Jake"

    def test_each_template_has_required_fields(self):
        """Verify each template has id, name, and thumbnail_url."""
        templates = list_templates()
        for t in templates:
            assert "id" in t
            assert "name" in t
            assert "thumbnail_url" in t
            assert isinstance(t["id"], str)
            assert isinstance(t["name"], str)
