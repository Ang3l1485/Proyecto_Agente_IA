from django.db import migrations

SQL_ADD_IS_ACTIVE = r"""
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = 'agent_prompt' AND column_name = 'is_active'
    ) THEN
        ALTER TABLE public.agent_prompt
        ADD COLUMN is_active boolean NOT NULL DEFAULT TRUE;
    END IF;
END $$;
"""

SQL_REMOVE_IS_ACTIVE = r"""
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = 'agent_prompt' AND column_name = 'is_active'
    ) THEN
        ALTER TABLE public.agent_prompt
        DROP COLUMN is_active;
    END IF;
END $$;
"""

class Migration(migrations.Migration):

    dependencies = [
        ('agent', '0005_rename_business_fk_to_client'),
    ]

    operations = [
        migrations.RunSQL(sql=SQL_ADD_IS_ACTIVE, reverse_sql=SQL_REMOVE_IS_ACTIVE),
    ]
