# Generated migration to add part and skill columns to questions table

from django.db import migrations, connection


def add_part_skill_columns(apps, schema_editor):
    """Add part and skill columns to questions table"""
    db_vendor = connection.vendor
    
    with connection.cursor() as cursor:
        if db_vendor == 'postgresql':
            # PostgreSQL supports IF NOT EXISTS
            cursor.execute("""
                DO $$ 
                BEGIN
                    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                                   WHERE table_name='questions' AND column_name='part') THEN
                        ALTER TABLE questions ADD COLUMN part TEXT NULL;
                    END IF;
                    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                                   WHERE table_name='questions' AND column_name='skill') THEN
                        ALTER TABLE questions ADD COLUMN skill TEXT NULL;
                    END IF;
                END $$;
            """)
        elif db_vendor == 'mysql' or db_vendor == 'mariadb':
            # MySQL/MariaDB - check before adding
            cursor.execute("""
                SELECT COUNT(*) FROM information_schema.columns 
                WHERE table_schema = DATABASE() 
                AND table_name = 'questions' 
                AND column_name = 'part'
            """)
            if cursor.fetchone()[0] == 0:
                cursor.execute("ALTER TABLE questions ADD COLUMN part TEXT NULL")
            
            cursor.execute("""
                SELECT COUNT(*) FROM information_schema.columns 
                WHERE table_schema = DATABASE() 
                AND table_name = 'questions' 
                AND column_name = 'skill'
            """)
            if cursor.fetchone()[0] == 0:
                cursor.execute("ALTER TABLE questions ADD COLUMN skill TEXT NULL")
        else:
            # SQLite or other - try to add, ignore if exists
            try:
                cursor.execute("ALTER TABLE questions ADD COLUMN part TEXT NULL")
            except Exception:
                pass
            try:
                cursor.execute("ALTER TABLE questions ADD COLUMN skill TEXT NULL")
            except Exception:
                pass


def remove_part_skill_columns(apps, schema_editor):
    """Remove part and skill columns from questions table"""
    db_vendor = connection.vendor
    
    with connection.cursor() as cursor:
        if db_vendor == 'postgresql':
            cursor.execute("""
                DO $$ 
                BEGIN
                    IF EXISTS (SELECT 1 FROM information_schema.columns 
                              WHERE table_name='questions' AND column_name='part') THEN
                        ALTER TABLE questions DROP COLUMN part;
                    END IF;
                    IF EXISTS (SELECT 1 FROM information_schema.columns 
                              WHERE table_name='questions' AND column_name='skill') THEN
                        ALTER TABLE questions DROP COLUMN skill;
                    END IF;
                END $$;
            """)
        elif db_vendor == 'mysql' or db_vendor == 'mariadb':
            cursor.execute("""
                SELECT COUNT(*) FROM information_schema.columns 
                WHERE table_schema = DATABASE() 
                AND table_name = 'questions' 
                AND column_name = 'part'
            """)
            if cursor.fetchone()[0] > 0:
                cursor.execute("ALTER TABLE questions DROP COLUMN part")
            
            cursor.execute("""
                SELECT COUNT(*) FROM information_schema.columns 
                WHERE table_schema = DATABASE() 
                AND table_name = 'questions' 
                AND column_name = 'skill'
            """)
            if cursor.fetchone()[0] > 0:
                cursor.execute("ALTER TABLE questions DROP COLUMN skill")
        else:
            # SQLite doesn't support DROP COLUMN easily, skip
            pass


class Migration(migrations.Migration):

    dependencies = [
        ('tests', '0002_examanswer_examinstancequestion'),
    ]

    operations = [
        migrations.RunPython(add_part_skill_columns, remove_part_skill_columns),
    ]

