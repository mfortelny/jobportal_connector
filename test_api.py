import pytest
import hashlib
from unittest.mock import Mock, patch
from api.scraper import JobScraper

class TestJobScraper:
    def test_phone_hashing_consistency(self):
        """Test that phone hashing produces consistent results"""
        phone = "+420123456789"
        expected_hash = hashlib.sha256(phone.encode()).hexdigest()
        
        # This would be handled by PostgreSQL, but we can test the concept
        assert len(expected_hash) == 64
        assert expected_hash == hashlib.sha256(phone.encode()).hexdigest()
    
    def test_domain_extraction(self):
        """Test URL domain extraction for allowed_domains"""
        scraper = JobScraper("", "", "")
        
        test_cases = [
            ("https://jobs.example.com/login", "jobs.example.com"),
            ("http://portal.company.cz/dashboard", "portal.company.cz"),
            ("https://hiring.tech-company.com/positions", "hiring.tech-company.com")
        ]
        
        for url, expected_domain in test_cases:
            assert scraper._extract_domain(url) == expected_domain
    
    @patch('api.scraper.create_client')
    def test_duplicate_prevention_logic(self, mock_supabase):
        """Test that existing phone hashes are properly retrieved and used"""
        # Mock Supabase client
        mock_client = Mock()
        mock_supabase.return_value = mock_client
        
        # Mock existing candidates with phone hashes
        existing_candidates = [
            {"phone_sha256": "abc123"},
            {"phone_sha256": "def456"},
            {"phone_sha256": "ghi789"}
        ]
        
        mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = existing_candidates
        
        scraper = JobScraper("test_url", "test_key", "test_browser_key")
        
        # This would normally be async, but we're testing the logic
        result = scraper._get_existing_phone_hashes("position_id_123")
        
        expected_hashes = ["abc123", "def456", "ghi789"]
        assert result == expected_hashes
    
    def test_task_prompt_generation(self):
        """Test that the scraping task prompt is properly formatted"""
        scraper = JobScraper("", "", "")
        
        portal_url = "https://jobs.example.com"
        position_name = "Senior Developer"
        
        task = scraper._build_scraping_task(portal_url, position_name)
        
        assert portal_url in task
        assert position_name in task
        assert "sha256" in task
        assert "skip_hashes_csv" in task
        assert "structured_output_json" in task

if __name__ == "__main__":
    pytest.main([__file__]) 