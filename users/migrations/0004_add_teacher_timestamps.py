# Generated manually to fix missing created_at and updated_at columns in teachers table

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0003_alter_student_commitment_status'),
    ]

    operations = [
        migrations.RunSQL(
            # Add created_at column if it doesn't exist
            sql="""
                DO $$ 
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1 FROM information_schema.columns 
                        WHERE table_name = 'teachers' AND column_name = 'created_at'
                    ) THEN
                        ALTER TABLE teachers ADD COLUMN created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();
                    END IF;
                END $$;
            """,
            reverse_sql="""
                ALTER TABLE teachers DROP COLUMN IF EXISTS created_at;
            """
        ),
        migrations.RunSQL(
            # Add updated_at column if it doesn't exist
            sql="""
                DO $$ 
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1 FROM information_schema.columns 
                        WHERE table_name = 'teachers' AND column_name = 'updated_at'
                    ) THEN
                        ALTER TABLE teachers ADD COLUMN updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();
                    END IF;
                END $$;
            """,
            reverse_sql="""
                ALTER TABLE teachers DROP COLUMN IF EXISTS updated_at;
            """
        ),
    ]

