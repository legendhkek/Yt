#!/usr/bin/env python3
"""
BOT TEST SUITE
Comprehensive testing for the Telegram YouTube View Bot.

Author: Manus Bot Development
Version: 2.0
"""

import unittest
import sys
import os
import json
import tempfile
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta

# Add bot directory to path
sys.path.insert(0, os.path.dirname(__file__))

from utils import (
    LRUCache, Validator, Formatter, SecurityUtils, 
    JSONUtils, Statistics, FileUtils
)
from config import Config, validate_config

class TestLRUCache(unittest.TestCase):
    """Test LRU Cache implementation"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.cache = LRUCache(max_size=3, expiry_time=10)
    
    def test_set_and_get(self):
        """Test setting and getting values"""
        self.cache.set("key1", "value1")
        self.assertEqual(self.cache.get("key1"), "value1")
    
    def test_cache_size_limit(self):
        """Test cache size limit"""
        self.cache.set("key1", "value1")
        self.cache.set("key2", "value2")
        self.cache.set("key3", "value3")
        self.cache.set("key4", "value4")
        
        self.assertEqual(self.cache.size(), 3)
        self.assertIsNone(self.cache.get("key1"))
    
    def test_cache_clear(self):
        """Test clearing cache"""
        self.cache.set("key1", "value1")
        self.cache.clear()
        self.assertEqual(self.cache.size(), 0)

class TestValidator(unittest.TestCase):
    """Test input validation"""
    
    def test_valid_youtube_url(self):
        """Test YouTube URL validation"""
        valid_urls = [
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "https://youtu.be/dQw4w9WgXcQ",
            "https://www.youtube.com/embed/dQw4w9WgXcQ",
        ]
        
        for url in valid_urls:
            self.assertTrue(Validator.is_valid_youtube_url(url))
    
    def test_invalid_youtube_url(self):
        """Test invalid YouTube URL"""
        invalid_urls = [
            "https://www.google.com",
            "https://www.youtube.com/",
            "not a url",
        ]
        
        for url in invalid_urls:
            self.assertFalse(Validator.is_valid_youtube_url(url))
    
    def test_extract_video_id(self):
        """Test video ID extraction"""
        url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        video_id = Validator.extract_video_id(url)
        self.assertEqual(video_id, "dQw4w9WgXcQ")
    
    def test_valid_email(self):
        """Test email validation"""
        valid_emails = [
            "test@example.com",
            "user.name@example.co.uk",
            "test123@test.org",
        ]
        
        for email in valid_emails:
            self.assertTrue(Validator.is_valid_email(email))
    
    def test_invalid_email(self):
        """Test invalid email"""
        invalid_emails = [
            "invalid.email",
            "@example.com",
            "test@",
        ]
        
        for email in invalid_emails:
            self.assertFalse(Validator.is_valid_email(email))
    
    def test_sanitize_input(self):
        """Test input sanitization"""
        dirty_input = "  <script>alert('xss')</script>  "
        clean_input = Validator.sanitize_input(dirty_input)
        self.assertNotIn("<", clean_input)
        self.assertNotIn(">", clean_input)

class TestFormatter(unittest.TestCase):
    """Test text formatting"""
    
    def test_format_number(self):
        """Test number formatting"""
        self.assertEqual(Formatter.format_number(1000), "1,000")
        self.assertEqual(Formatter.format_number(1000000), "1,000,000")
    
    def test_format_bytes(self):
        """Test bytes formatting"""
        self.assertEqual(Formatter.format_bytes(1024), "1.00 KB")
        self.assertEqual(Formatter.format_bytes(1048576), "1.00 MB")
    
    def test_format_duration(self):
        """Test duration formatting"""
        self.assertEqual(Formatter.format_duration(30), "30s")
        self.assertEqual(Formatter.format_duration(90), "1m 30s")
        self.assertEqual(Formatter.format_duration(3600), "1h 0m")
    
    def test_format_percentage(self):
        """Test percentage formatting"""
        self.assertEqual(Formatter.format_percentage(50, 100), "50.0%")
        self.assertEqual(Formatter.format_percentage(1, 3), "33.3%")
    
    def test_truncate_text(self):
        """Test text truncation"""
        text = "This is a long text that should be truncated"
        truncated = Formatter.truncate_text(text, max_length=20)
        self.assertLessEqual(len(truncated), 20)
        self.assertTrue(truncated.endswith("..."))

class TestSecurityUtils(unittest.TestCase):
    """Test security utilities"""
    
    def test_hash_string(self):
        """Test string hashing"""
        text = "test"
        hash_sha256 = SecurityUtils.hash_string(text, "sha256")
        self.assertEqual(len(hash_sha256), 64)
        
        hash_md5 = SecurityUtils.hash_string(text, "md5")
        self.assertEqual(len(hash_md5), 32)
    
    def test_base64_encoding(self):
        """Test base64 encoding/decoding"""
        text = "Hello, World!"
        encoded = SecurityUtils.encode_base64(text)
        decoded = SecurityUtils.decode_base64(encoded)
        self.assertEqual(decoded, text)
    
    def test_mask_sensitive_data(self):
        """Test sensitive data masking"""
        data = "1234567890"
        masked = SecurityUtils.mask_sensitive_data(data, visible_chars=4)
        self.assertTrue(masked.startswith("1234"))
        self.assertTrue(masked.endswith("*" * 6))

class TestStatistics(unittest.TestCase):
    """Test statistical functions"""
    
    def test_calculate_average(self):
        """Test average calculation"""
        values = [1, 2, 3, 4, 5]
        avg = Statistics.calculate_average(values)
        self.assertEqual(avg, 3.0)
    
    def test_calculate_median(self):
        """Test median calculation"""
        values = [1, 2, 3, 4, 5]
        median = Statistics.calculate_median(values)
        self.assertEqual(median, 3)
    
    def test_calculate_std_dev(self):
        """Test standard deviation calculation"""
        values = [1, 2, 3, 4, 5]
        std_dev = Statistics.calculate_std_dev(values)
        self.assertGreater(std_dev, 0)

class TestJSONUtils(unittest.TestCase):
    """Test JSON utilities"""
    
    def test_save_and_load_json(self):
        """Test JSON save and load"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            temp_file = f.name
        
        try:
            data = {"key": "value", "number": 42}
            JSONUtils.save_json(data, temp_file)
            loaded_data = JSONUtils.load_json(temp_file)
            self.assertEqual(loaded_data, data)
        finally:
            if os.path.exists(temp_file):
                os.remove(temp_file)
    
    def test_merge_json(self):
        """Test JSON merging"""
        dict1 = {"a": 1, "b": 2}
        dict2 = {"b": 3, "c": 4}
        merged = JSONUtils.merge_json(dict1, dict2)
        self.assertEqual(merged, {"a": 1, "b": 3, "c": 4})
    
    def test_get_nested_value(self):
        """Test nested value retrieval"""
        data = {"user": {"name": "John", "age": 30}}
        value = JSONUtils.get_nested_value(data, "user.name")
        self.assertEqual(value, "John")

class TestFileUtils(unittest.TestCase):
    """Test file utilities"""
    
    def test_file_operations(self):
        """Test file read/write operations"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            temp_file = f.name
        
        try:
            content = "Test content"
            FileUtils.write_file(temp_file, content)
            self.assertTrue(FileUtils.file_exists(temp_file))
            
            read_content = FileUtils.read_file(temp_file)
            self.assertEqual(read_content, content)
        finally:
            if os.path.exists(temp_file):
                os.remove(temp_file)
    
    def test_create_directory(self):
        """Test directory creation"""
        with tempfile.TemporaryDirectory() as temp_dir:
            new_dir = os.path.join(temp_dir, "test_dir")
            result = FileUtils.create_directory(new_dir)
            self.assertTrue(result)
            self.assertTrue(os.path.exists(new_dir))

class TestConfiguration(unittest.TestCase):
    """Test configuration management"""
    
    def test_validate_config(self):
        """Test configuration validation"""
        valid, message = validate_config()
        self.assertIsInstance(valid, bool)
        self.assertIsInstance(message, str)
    
    def test_config_singleton(self):
        """Test configuration singleton"""
        config1 = Config()
        config2 = Config()
        self.assertIs(config1, config2)
    
    def test_config_to_dict(self):
        """Test configuration to dictionary"""
        config = Config()
        config_dict = config.to_dict()
        self.assertIsInstance(config_dict, dict)
        self.assertIn("BOT_NAME", config_dict)

class TestIntegration(unittest.TestCase):
    """Integration tests"""
    
    def test_youtube_url_extraction(self):
        """Test YouTube URL extraction workflow"""
        url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        
        # Validate URL
        is_valid = Validator.is_valid_youtube_url(url)
        self.assertTrue(is_valid)
        
        # Extract video ID
        video_id = Validator.extract_video_id(url)
        self.assertEqual(video_id, "dQw4w9WgXcQ")
    
    def test_data_formatting_workflow(self):
        """Test data formatting workflow"""
        # Format numbers
        formatted_number = Formatter.format_number(1000000)
        self.assertEqual(formatted_number, "1,000,000")
        
        # Format bytes
        formatted_bytes = Formatter.format_bytes(1048576)
        self.assertEqual(formatted_bytes, "1.00 MB")
        
        # Format duration
        formatted_duration = Formatter.format_duration(3661)
        self.assertIn("h", formatted_duration)
        self.assertIn("m", formatted_duration)

def run_tests():
    """Run all tests"""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestLRUCache))
    suite.addTests(loader.loadTestsFromTestCase(TestValidator))
    suite.addTests(loader.loadTestsFromTestCase(TestFormatter))
    suite.addTests(loader.loadTestsFromTestCase(TestSecurityUtils))
    suite.addTests(loader.loadTestsFromTestCase(TestStatistics))
    suite.addTests(loader.loadTestsFromTestCase(TestJSONUtils))
    suite.addTests(loader.loadTestsFromTestCase(TestFileUtils))
    suite.addTests(loader.loadTestsFromTestCase(TestConfiguration))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegration))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
