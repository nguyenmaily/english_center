"""
Django management command để thêm dữ liệu mẫu vào ngân hàng câu hỏi
Tạo các câu hỏi đơn và nhóm câu hỏi cho các kỹ năng khác nhau
"""
from django.core.management.base import BaseCommand
from django.db import connection
from django.utils import timezone
import uuid
import random


class Command(BaseCommand):
    help = 'Thêm dữ liệu mẫu vào ngân hàng câu hỏi (câu hỏi đơn và nhóm câu hỏi)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            default=50,
            help='Số lượng câu hỏi đơn cần tạo (mặc định: 50)',
        )
        parser.add_argument(
            '--groups',
            type=int,
            default=10,
            help='Số lượng nhóm câu hỏi cần tạo (mặc định: 10)',
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Xóa dữ liệu cũ trước khi tạo mới',
        )

    def handle(self, *args, **options):
        count = options['count']
        groups_count = options['groups']
        
        if options['clear']:
            self.stdout.write(self.style.WARNING('Dang xoa du lieu cu...'))
            self.clear_data()
        
        self.stdout.write(self.style.SUCCESS('Bat dau them du lieu vao ngan hang cau hoi...'))
        
        # Tạo nhóm câu hỏi
        question_groups = self.create_question_groups(groups_count)
        self.stdout.write(self.style.SUCCESS(f'Da tao {len(question_groups)} nhom cau hoi'))
        
        # Tạo câu hỏi đơn
        single_questions = self.create_single_questions(count)
        self.stdout.write(self.style.SUCCESS(f'Da tao {len(single_questions)} cau hoi don'))
        
        # Tạo câu hỏi thuộc nhóm
        group_questions = self.create_group_questions(question_groups)
        self.stdout.write(self.style.SUCCESS(f'Da tao {len(group_questions)} cau hoi thuoc nhom'))
        
        self.stdout.write(self.style.SUCCESS(f'\nHoan thanh! Tong cong:'))
        self.stdout.write(f'  - Nhom cau hoi: {len(question_groups)}')
        self.stdout.write(f'  - Cau hoi don: {len(single_questions)}')
        self.stdout.write(f'  - Cau hoi trong nhom: {len(group_questions)}')
        self.stdout.write(f'  - Tong cau hoi: {len(single_questions) + len(group_questions)}')

    def clear_data(self):
        """Xóa dữ liệu cũ trong ngân hàng câu hỏi"""
        with connection.cursor() as cursor:
            try:
                cursor.execute('DELETE FROM questions')
                self.stdout.write('  Da xoa questions')
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'  Khong the xoa questions: {e}'))
            
            try:
                cursor.execute('DELETE FROM question_groups')
                self.stdout.write('  Da xoa question_groups')
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'  Khong the xoa question_groups: {e}'))

    def create_question_groups(self, count):
        """Tạo nhóm câu hỏi với context, part, skill"""
        question_groups = []
        
        parts = ['3', '4', '6', '7']  # Các part thường có nhóm câu hỏi
        skills = ['listening', 'reading']
        
        # Context mẫu cho các nhóm câu hỏi
        listening_contexts = [
            "Man: Hi, I'm calling about the job position you advertised.\nWoman: Great! Can you tell me about your experience?\nMan: I've worked in sales for five years.\nWoman: That sounds perfect. Can you come in for an interview tomorrow?",
            "Woman: Excuse me, where is the nearest restroom?\nMan: It's down the hall, on your right.\nWoman: Thank you so much!\nMan: You're welcome.",
            "Man: I'd like to make a reservation for two people tonight at 7 PM.\nWoman: I'm sorry, we're fully booked tonight. Would 8 PM work for you?\nMan: Yes, that would be fine.\nWoman: Great, I'll reserve a table for two at 8 PM.",
            "Woman: The weather forecast says it will rain tomorrow.\nMan: Really? I was planning to go to the beach.\nWoman: Maybe you should check again in the morning.\nMan: Good idea, thanks for letting me know.",
            "Man: Can you help me find a book about history?\nWoman: Sure, the history section is on the second floor.\nMan: Thank you. How do I get there?\nWoman: Take the elevator or stairs at the end of this aisle.",
        ]
        
        reading_contexts = [
            "The city council announced yesterday that it will be implementing new recycling programs starting next month. Residents will receive special bins for paper, plastic, and glass. The program aims to reduce waste by 30% over the next year. Collection will occur every Tuesday and Friday.",
            "Recent studies have shown that regular exercise can significantly improve mental health. Researchers found that people who exercise at least three times a week report lower levels of stress and anxiety. The study followed 1,000 participants over a period of two years.",
            "The local library is expanding its hours to better serve the community. Beginning next week, the library will be open from 8 AM to 9 PM on weekdays and 10 AM to 6 PM on weekends. New services include free computer classes and children's reading programs.",
            "Technology companies are increasingly focusing on sustainable practices. Many are switching to renewable energy sources and reducing their carbon footprint. This trend is driven by both environmental concerns and customer demand for eco-friendly products.",
            "The annual music festival will take place in Central Park from June 15th to June 17th. This year's event features over 50 artists from around the world. Tickets go on sale next Monday and are expected to sell out quickly.",
        ]
        
        with connection.cursor() as cursor:
            for i in range(count):
                group_id = uuid.uuid4()
                part = random.choice(parts)
                skill = random.choice(skills)
                
                # Chọn context phù hợp với skill
                if skill == 'listening':
                    context = random.choice(listening_contexts)
                else:
                    context = random.choice(reading_contexts)
                
                # Một số nhóm có audio, một số có image
                audio_file = None
                image_file = None
                
                if skill == 'listening' and random.random() > 0.3:  # 70% có audio
                    audio_file = f'/media/question_groups/audio_sample_{i+1}.mp3'
                
                if skill == 'reading' and random.random() > 0.5:  # 50% có image
                    image_file = f'/media/question_groups/image_sample_{i+1}.jpg'
                
                cursor.execute("""
                    INSERT INTO question_groups (id, part, skill, context, audio_file, image_file, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, [group_id, part, skill, context, audio_file, image_file, 
                      timezone.now(), timezone.now()])
                
                question_groups.append({
                    'id': group_id,
                    'part': part,
                    'skill': skill
                })
        
        return question_groups

    def create_single_questions(self, count):
        """Tạo câu hỏi đơn với các part, skill, difficulty khác nhau"""
        questions = []
        
        parts = ['1', '2', '5']  # Các part thường có câu hỏi đơn
        skills = ['listening', 'reading', 'speaking', 'writing']
        difficulties = ['easy', 'medium', 'hard']
        
        # Câu hỏi mẫu cho từng skill
        question_templates = {
            'listening': [
                {
                    'text': 'What is the main topic of the conversation?',
                    'options': {
                        'A': 'Job interview',
                        'B': 'Restaurant reservation',
                        'C': 'Hotel booking',
                        'D': 'Flight schedule'
                    },
                    'correct': 'A'
                },
                {
                    'text': 'Where does the conversation most likely take place?',
                    'options': {
                        'A': 'At a restaurant',
                        'B': 'In an office',
                        'C': 'At a library',
                        'D': 'In a store'
                    },
                    'correct': 'B'
                },
                {
                    'text': 'What time will the meeting start?',
                    'options': {
                        'A': '9:00 AM',
                        'B': '10:00 AM',
                        'C': '11:00 AM',
                        'D': '2:00 PM'
                    },
                    'correct': 'B'
                },
            ],
            'reading': [
                {
                    'text': 'What is the main idea of the passage?',
                    'options': {
                        'A': 'The benefits of exercise',
                        'B': 'How to start a fitness program',
                        'C': 'The history of sports',
                        'D': 'Types of physical activities'
                    },
                    'correct': 'A'
                },
                {
                    'text': 'According to the passage, what should you do first?',
                    'options': {
                        'A': 'Buy equipment',
                        'B': 'Consult a doctor',
                        'C': 'Join a gym',
                        'D': 'Find a trainer'
                    },
                    'correct': 'B'
                },
                {
                    'text': 'The word "significant" in paragraph 2 is closest in meaning to:',
                    'options': {
                        'A': 'small',
                        'B': 'important',
                        'C': 'temporary',
                        'D': 'difficult'
                    },
                    'correct': 'B'
                },
            ],
            'speaking': [
                {
                    'text': 'Describe your favorite place to visit.',
                    'options': {
                        'A': 'Multiple choice option A',
                        'B': 'Multiple choice option B',
                        'C': 'Multiple choice option C',
                        'D': 'Multiple choice option D'
                    },
                    'correct': ''
                },
                {
                    'text': 'What are the advantages of living in a big city?',
                    'options': {
                        'A': 'Multiple choice option A',
                        'B': 'Multiple choice option B',
                        'C': 'Multiple choice option C',
                        'D': 'Multiple choice option D'
                    },
                    'correct': ''
                },
            ],
            'writing': [
                {
                    'text': 'Write a paragraph about your daily routine.',
                    'options': {
                        'A': 'Multiple choice option A',
                        'B': 'Multiple choice option B',
                        'C': 'Multiple choice option C',
                        'D': 'Multiple choice option D'
                    },
                    'correct': ''
                },
                {
                    'text': 'Explain the importance of learning English.',
                    'options': {
                        'A': 'Multiple choice option A',
                        'B': 'Multiple choice option B',
                        'C': 'Multiple choice option C',
                        'D': 'Multiple choice option D'
                    },
                    'correct': ''
                },
            ],
        }
        
        with connection.cursor() as cursor:
            for i in range(count):
                question_id = uuid.uuid4()
                part = random.choice(parts)
                skill = random.choice(skills)
                difficulty = random.choice(difficulties)
                
                # Chọn template câu hỏi
                templates = question_templates.get(skill, question_templates['listening'])
                template = random.choice(templates)
                
                text = template['text']
                option_a = template['options'].get('A', '')
                option_b = template['options'].get('B', '')
                option_c = template['options'].get('C', '')
                option_d = template['options'].get('D', '')
                correct_answer = template['correct']
                
                # Một số câu hỏi listening có audio
                audio_file = None
                if skill == 'listening' and random.random() > 0.5:
                    audio_file = f'/media/questions/audio_{i+1}.mp3'
                
                cursor.execute("""
                    INSERT INTO questions (id, group_id, part, skill, text, option_a, option_b, option_c, option_d, 
                                          correct_answer, audio_file, difficulty, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, [question_id, None, part, skill, text, option_a, option_b, option_c, option_d,
                      correct_answer, audio_file, difficulty, timezone.now(), timezone.now()])
                
                questions.append({'id': question_id})
        
        return questions

    def create_group_questions(self, question_groups):
        """Tạo câu hỏi thuộc các nhóm câu hỏi"""
        group_questions = []
        
        # Câu hỏi mẫu cho nhóm
        group_question_templates = [
            {
                'text': 'What is the main purpose of the conversation?',
                'options': {
                    'A': 'To make a reservation',
                    'B': 'To cancel an appointment',
                    'C': 'To ask for directions',
                    'D': 'To complain about service'
                },
                'correct': 'A'
            },
            {
                'text': 'Where does this conversation most likely take place?',
                'options': {
                    'A': 'At a restaurant',
                    'B': 'In a hotel',
                    'C': 'At a library',
                    'D': 'In a store'
                },
                'correct': 'A'
            },
            {
                'text': 'What will the man probably do next?',
                'options': {
                    'A': 'Leave immediately',
                    'B': 'Wait for a call',
                    'C': 'Make another appointment',
                    'D': 'Ask more questions'
                },
                'correct': 'B'
            },
            {
                'text': 'According to the passage, what is mentioned as a benefit?',
                'options': {
                    'A': 'Lower costs',
                    'B': 'Better quality',
                    'C': 'Faster service',
                    'D': 'More options'
                },
                'correct': 'A'
            },
            {
                'text': 'The word "implement" in paragraph 1 is closest in meaning to:',
                'options': {
                    'A': 'cancel',
                    'B': 'start',
                    'C': 'discuss',
                    'D': 'improve'
                },
                'correct': 'B'
            },
            {
                'text': 'What can be inferred from the passage?',
                'options': {
                    'A': 'The program will be expensive',
                    'B': 'Many people support the idea',
                    'C': 'It will take years to complete',
                    'D': 'There are some concerns'
                },
                'correct': 'B'
            },
        ]
        
        with connection.cursor() as cursor:
            for group in question_groups:
                # Mỗi nhóm có 3-5 câu hỏi
                num_questions = random.randint(3, 5)
                
                for i in range(num_questions):
                    question_id = uuid.uuid4()
                    template = random.choice(group_question_templates)
                    
                    text = template['text']
                    option_a = template['options'].get('A', '')
                    option_b = template['options'].get('B', '')
                    option_c = template['options'].get('C', '')
                    option_d = template['options'].get('D', '')
                    correct_answer = template['correct']
                    difficulty = random.choice(['easy', 'medium', 'hard'])
                    
                    cursor.execute("""
                        INSERT INTO questions (id, group_id, part, skill, text, option_a, option_b, option_c, option_d, 
                                              correct_answer, audio_file, difficulty, created_at, updated_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, [question_id, group['id'], group['part'], group['skill'], text, 
                          option_a, option_b, option_c, option_d, correct_answer, None, 
                          difficulty, timezone.now(), timezone.now()])
                    
                    group_questions.append({'id': question_id})
        
        return group_questions

