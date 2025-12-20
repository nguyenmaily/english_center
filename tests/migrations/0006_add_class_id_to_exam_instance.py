# Generated migration to add class_id to exam_instances

from django.db import migrations, connection


def add_class_id_column(apps, schema_editor):
    """Add class_id column to exam_instances table"""
    db_vendor = connection.vendor
    
    with connection.cursor() as cursor:
        if db_vendor == 'postgresql':
            # PostgreSQL supports IF NOT EXISTS
            cursor.execute("""
                DO $$ 
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1 FROM information_schema.columns 
                        WHERE table_name = 'exam_instances' 
                        AND column_name = 'class_id'
                    ) THEN
                        ALTER TABLE exam_instances 
                        ADD COLUMN class_id UUID NULL;
                    END IF;
                END $$;
            """)
        elif db_vendor == 'mysql' or db_vendor == 'mariadb':
            # MySQL/MariaDB - check before adding
            cursor.execute("""
                SELECT COUNT(*) FROM information_schema.columns 
                WHERE table_schema = DATABASE() 
                AND table_name = 'exam_instances' 
                AND column_name = 'class_id'
            """)
            if cursor.fetchone()[0] == 0:
                cursor.execute("ALTER TABLE exam_instances ADD COLUMN class_id CHAR(36) NULL")
        else:
            # SQLite or other - try to add, ignore if exists
            try:
                cursor.execute("ALTER TABLE exam_instances ADD COLUMN class_id TEXT NULL")
            except Exception:
                pass


def remove_class_id_column(apps, schema_editor):
    """Remove class_id column from exam_instances table"""
    db_vendor = connection.vendor
    
    with connection.cursor() as cursor:
        if db_vendor == 'postgresql':
            cursor.execute("""
                DO $$ 
                BEGIN
                    IF EXISTS (
                        SELECT 1 FROM information_schema.columns 
                        WHERE table_name = 'exam_instances' 
                        AND column_name = 'class_id'
                    ) THEN
                        ALTER TABLE exam_instances DROP COLUMN class_id;
                    END IF;
                END $$;
            """)
        elif db_vendor == 'mysql' or db_vendor == 'mariadb':
            cursor.execute("""
                SELECT COUNT(*) FROM information_schema.columns 
                WHERE table_schema = DATABASE() 
                AND table_name = 'exam_instances' 
                AND column_name = 'class_id'
            """)
            if cursor.fetchone()[0] > 0:
                cursor.execute("ALTER TABLE exam_instances DROP COLUMN class_id")
        else:
            # SQLite doesn't support DROP COLUMN easily, skip
            pass


class Migration(migrations.Migration):

    dependencies = [
        ('tests', '0004_add_audio_file_to_questions'),
    ]

    operations = [
        migrations.RunPython(add_class_id_column, remove_class_id_column),
    ]

