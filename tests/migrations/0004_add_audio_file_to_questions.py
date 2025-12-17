# Generated migration to add audio_file column to questions table

from django.db import migrations, connection


def add_audio_file_column(apps, schema_editor):
    """Add audio_file column to questions table"""
    db_vendor = connection.vendor
    
    with connection.cursor() as cursor:
        if db_vendor == 'postgresql':
            # PostgreSQL supports IF NOT EXISTS
            cursor.execute("""
                DO $$ 
                BEGIN
                    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                                   WHERE table_name='questions' AND column_name='audio_file') THEN
                        ALTER TABLE questions ADD COLUMN audio_file TEXT NULL;
                    END IF;
                END $$;
            """)
        elif db_vendor == 'mysql' or db_vendor == 'mariadb':
            # MySQL/MariaDB - check before adding
            cursor.execute("""
                SELECT COUNT(*) FROM information_schema.columns 
                WHERE table_schema = DATABASE() 
                AND table_name = 'questions' 
                AND column_name = 'audio_file'
            """)
            if cursor.fetchone()[0] == 0:
                cursor.execute("ALTER TABLE questions ADD COLUMN audio_file TEXT NULL")
        else:
            # SQLite or other - try to add, ignore if exists
            try:
                cursor.execute("ALTER TABLE questions ADD COLUMN audio_file TEXT NULL")
            except Exception:
                pass


def remove_audio_file_column(apps, schema_editor):
    """Remove audio_file column from questions table"""
    db_vendor = connection.vendor
    
    with connection.cursor() as cursor:
        if db_vendor == 'postgresql':
            cursor.execute("""
                DO $$ 
                BEGIN
                    IF EXISTS (SELECT 1 FROM information_schema.columns 
                              WHERE table_name='questions' AND column_name='audio_file') THEN
                        ALTER TABLE questions DROP COLUMN audio_file;
                    END IF;
                END $$;
            """)
        elif db_vendor == 'mysql' or db_vendor == 'mariadb':
            cursor.execute("""
                SELECT COUNT(*) FROM information_schema.columns 
                WHERE table_schema = DATABASE() 
                AND table_name = 'questions' 
                AND column_name = 'audio_file'
            """)
            if cursor.fetchone()[0] > 0:
                cursor.execute("ALTER TABLE questions DROP COLUMN audio_file")
        else:
            # SQLite doesn't support DROP COLUMN easily, skip
            pass


class Migration(migrations.Migration):

    dependencies = [
        ('tests', '0003_add_part_skill_to_questions'),
    ]

    operations = [
        migrations.RunPython(add_audio_file_column, remove_audio_file_column),
    ]

