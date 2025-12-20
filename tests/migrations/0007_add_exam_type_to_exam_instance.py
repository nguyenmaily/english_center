# Generated migration to add exam_type to exam_instances table

from django.db import migrations

class Migration(migrations.Migration):

    dependencies = [
        ('tests', '0006_add_class_id_to_exam_instance'),
    ]

    operations = [
        migrations.RunSQL(
            # Add exam_type column if it doesn't exist
            sql="""
                DO $$ 
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1 FROM information_schema.columns 
                        WHERE table_name = 'exam_instances' 
                        AND column_name = 'exam_type'
                    ) THEN
                        ALTER TABLE exam_instances 
                        ADD COLUMN exam_type VARCHAR(50) NULL;
                    END IF;
                END $$;
            """,
            reverse_sql="""
                ALTER TABLE exam_instances 
                DROP COLUMN IF EXISTS exam_type;
            """
        ),
    ]

