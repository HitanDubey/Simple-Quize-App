"""
Web Scraper Module for EchoQuest Pro
Fetches quiz questions from various web sources with caching and fast fallbacks
"""

import requests
import json
import random
import re
import time
import os
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import wikipedia
from typing import List, Dict, Any, Optional
from urllib.parse import quote_plus
import html

# Cache configuration
CACHE_DIR = 'question_cache'
CACHE_DURATION_HOURS = 24
os.makedirs(CACHE_DIR, exist_ok=True)

class QuestionScraper:
    """Main scraper class for fetching questions with caching"""
    
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        self.timeout = 5  # Reduced timeout for faster failures
        self.max_questions = 20
        
    def get_cached_questions(self, topic: str) -> Optional[List[Dict]]:
        """Get questions from cache if fresh"""
        cache_file = os.path.join(CACHE_DIR, f"{re.sub(r'[^a-zA-Z0-9]', '_', topic)}.json")
        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    cache_time = datetime.fromisoformat(data['cached_at'])
                    if datetime.now() - cache_time < timedelta(hours=CACHE_DURATION_HOURS):
                        print(f"✅ Using cached questions for: {topic}")
                        return data['questions']
            except Exception:
                pass
        return None
    
    def cache_questions(self, topic: str, questions: List[Dict]):
        """Cache questions for future use"""
        cache_file = os.path.join(CACHE_DIR, f"{re.sub(r'[^a-zA-Z0-9]', '_', topic)}.json")
        try:
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'cached_at': datetime.now().isoformat(),
                    'questions': questions
                }, f, ensure_ascii=False)
            print(f"💾 Cached {len(questions)} questions for: {topic}")
        except Exception as e:
            print(f"⚠️ Failed to cache: {e}")
    
    def fetch_questions(self, topic: str, num_questions: int = 20) -> List[Dict]:
        """Main method to fetch questions with caching"""
        
        # Check cache first
        cached = self.get_cached_questions(topic)
        if cached:
            return cached[:num_questions]
        
        print(f"🔍 Fetching questions for topic: {topic}")
        all_questions = []
        
        # Check if it's a math/table topic - use fast generation
        topic_lower = topic.lower()
        math_keywords = ['table', 'multiplication', 'math', 'addition', 'subtraction', 'division', 
                        'algebra', 'geometry', 'calculus', 'arithmetic']
        
        is_math_topic = any(keyword in topic_lower for keyword in math_keywords)
        
        if is_math_topic:
            print(f"📐 Math topic detected - using optimized generation")
            questions = self.generate_math_questions(topic, num_questions)
            all_questions.extend(questions)
        else:
            # Try Wikipedia first (faster than APIs)
            try:
                questions = self.fetch_from_wikipedia(topic)
                if questions:
                    all_questions.extend(questions)
                    print(f"✅ Wikipedia: {len(questions)} questions")
            except Exception as e:
                print(f"⚠️ Wikipedia failed: {e}")
            
            # Try Trivia API if needed
            if len(all_questions) < num_questions:
                try:
                    questions = self.fetch_from_trivia_api(topic)
                    if questions:
                        all_questions.extend(questions)
                        print(f"✅ Trivia API: {len(questions)} questions")
                except Exception as e:
                    print(f"⚠️ Trivia API failed: {e}")
        
        # Generate fallback questions if needed
        if len(all_questions) < num_questions:
            needed = num_questions - len(all_questions)
            questions = self.generate_fallback_questions(topic, needed)
            all_questions.extend(questions)
            print(f"✅ Generated: {len(questions)} questions")
        
        # Shuffle and limit
        random.shuffle(all_questions)
        final_questions = all_questions[:num_questions]
        
        # Cache for future use
        self.cache_questions(topic, final_questions)
        
        print(f"📚 Total questions prepared: {len(final_questions)}")
        return final_questions
    
    def generate_math_questions(self, topic: str, count: int) -> List[Dict]:
        """Special fast generator for math/table questions"""
        questions = []
        topic_lower = topic.lower()
        
        # Extract numbers from topic
        numbers = re.findall(r'\d+', topic)
        
        if 'table' in topic_lower and len(numbers) >= 2:
            start, end = int(numbers[0]), int(numbers[1])
            tables = list(range(start, end + 1))
            
            for i in range(count):
                table_num = random.choice(tables)
                multiplier = random.randint(1, 10)
                correct_answer = table_num * multiplier
                
                # Generate plausible wrong answers
                wrong_answers = [
                    correct_answer + table_num,
                    correct_answer - table_num,
                    correct_answer + random.randint(1, 5),
                    correct_answer - random.randint(1, 5)
                ]
                wrong_answers = [abs(x) for x in wrong_answers if x != correct_answer][:3]
                
                options = wrong_answers + [correct_answer]
                random.shuffle(options)
                correct_letter = chr(65 + options.index(correct_answer))
                
                question = {
                    'text': f'What is {table_num} × {multiplier}?',
                    'options': [str(opt) for opt in options],
                    'correct': correct_letter,
                    'explanation': f'{table_num} × {multiplier} = {table_num * multiplier}',
                    'difficulty': 'easy' if multiplier <= 5 else 'medium',
                    'source': 'MathGenerator'
                }
                questions.append(question)
        else:
            # Generic math questions
            operations = [
                ('+', lambda x, y: x + y, 'addition'),
                ('-', lambda x, y: x - y, 'subtraction'),
                ('×', lambda x, y: x * y, 'multiplication'),
                ('÷', lambda x, y: x // y if y != 0 else 1, 'division')
            ]
            
            for i in range(count):
                op_symbol, op_func, op_name = random.choice(operations)
                
                if op_symbol == '÷':
                    b = random.randint(2, 10)
                    a = b * random.randint(1, 10)
                else:
                    a = random.randint(1, 100)
                    b = random.randint(1, 100)
                
                correct = op_func(a, b)
                
                wrong_answers = [
                    correct + random.randint(1, 10),
                    correct - random.randint(1, 10),
                    abs(correct + random.randint(5, 15))
                ]
                wrong_answers = [x for x in wrong_answers if x != correct and x > 0][:3]
                
                options = wrong_answers + [correct]
                random.shuffle(options)
                correct_letter = chr(65 + options.index(correct))
                
                question = {
                    'text': f'What is {a} {op_symbol} {b}?',
                    'options': [str(opt) for opt in options],
                    'correct': correct_letter,
                    'explanation': f'{a} {op_symbol} {b} = {correct}',
                    'difficulty': 'easy' if a < 20 and b < 20 else 'medium',
                    'source': 'MathGenerator'
                }
                questions.append(question)
        
        return questions
    
    def fetch_from_wikipedia(self, topic: str) -> List[Dict]:
        """Fetch information from Wikipedia and create questions"""
        questions = []
        
        try:
            wikipedia.set_rate_limiting(True)
            search_results = wikipedia.search(topic, results=2)
            
            for page_title in search_results[:1]:  # Only first result for speed
                try:
                    page = wikipedia.page(page_title, auto_suggest=False)
                    summary = page.summary[:1000]
                    
                    sentences = re.split(r'[.!?]+', summary)
                    important_sentences = [s.strip() for s in sentences if len(s.strip()) > 30][:3]
                    
                    for sentence in important_sentences:
                        question_text = f"What is true about {page_title}?"
                        
                        options = [
                            sentence[:80] + "..." if len(sentence) > 80 else sentence,
                            f"A common misconception about {topic}",
                            f"An unrelated fact about {page_title}",
                            f"Something not mentioned in the article"
                        ]
                        
                        random.shuffle(options)
                        correct_letter = chr(65 + options.index(sentence[:80] + "..." if len(sentence) > 80 else sentence))
                        
                        question = {
                            'text': question_text,
                            'options': options,
                            'correct': correct_letter,
                            'explanation': f"According to Wikipedia: {sentence[:150]}",
                            'difficulty': 'medium',
                            'source': 'Wikipedia'
                        }
                        questions.append(question)
                        
                        if len(questions) >= 8:
                            break
                            
                except Exception as e:
                    continue
                    
        except Exception as e:
            print(f"Wikipedia error: {e}")
        
        return questions
    
    def fetch_from_trivia_api(self, topic: str) -> List[Dict]:
        """Fetch from trivia API with short timeout"""
        questions = []
        
        try:
            # Use a simpler, faster API
            url = "https://opentdb.com/api.php?amount=5&type=multiple"
            response = requests.get(url, timeout=3, headers=self.headers)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('response_code') == 0:
                    for item in data.get('results', []):
                        question_text = html.unescape(item['question'])
                        correct_answer = html.unescape(item['correct_answer'])
                        incorrect_answers = [html.unescape(ans) for ans in item['incorrect_answers']]
                        
                        options = incorrect_answers + [correct_answer]
                        random.shuffle(options)
                        correct_letter = chr(65 + options.index(correct_answer))
                        
                        question = {
                            'text': question_text,
                            'options': options,
                            'correct': correct_letter,
                            'explanation': f"The correct answer is: {correct_answer}",
                            'difficulty': item.get('difficulty', 'medium'),
                            'source': 'TriviaDB'
                        }
                        questions.append(question)
                        
        except Exception as e:
            print(f"Trivia API error: {e}")
        
        return questions
    
    def generate_fallback_questions(self, topic: str, count: int) -> List[Dict]:
        """Generate smart fallback questions"""
        questions = []
        
        templates = [
            f"What is the main purpose of {topic}?",
            f"Which of these best describes {topic}?",
            f"What is an important aspect of {topic}?",
            f"How does {topic} impact our daily lives?",
            f"What is a key benefit of understanding {topic}?",
            f"Who would benefit most from learning about {topic}?",
            f"What is a common application of {topic}?",
            f"What skill is most related to {topic}?",
            f"What tool is commonly used in {topic}?",
            f"What is a fundamental concept in {topic}?"
        ]
        
        for i in range(count):
            template = templates[i % len(templates)]
            
            options = [
                f"Understanding core principles",
                f"Practical application",
                f"Theoretical knowledge",
                f"Problem-solving skills"
            ]
            
            random.shuffle(options)
            correct_letter = random.choice(['A', 'B', 'C', 'D'])
            
            question = {
                'text': template,
                'options': options,
                'correct': correct_letter,
                'explanation': f"This relates to key concepts in {topic}.",
                'difficulty': random.choice(['easy', 'medium']),
                'source': 'SmartFallback'
            }
            questions.append(question)
        
        return questions

# Convenience function for easy import
def fetch_questions_from_web(topic: str, num_questions: int = 20) -> List[Dict]:
    """Main function to fetch questions with caching"""
    scraper = QuestionScraper()
    return scraper.fetch_questions(topic, num_questions)

# For backward compatibility
def generate_fallback_questions(topic: str, count: int = 20) -> List[Dict]:
    """Generate fallback questions"""
    scraper = QuestionScraper()
    return scraper.generate_fallback_questions(topic, count)