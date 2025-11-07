from django.db import migrations

RENAME_SQL = r"""
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = 'agent_agent' AND column_name = 'business_id'
    ) AND NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = 'agent_agent' AND column_name = 'client_id'
    ) THEN
        EXECUTE 'ALTER TABLE public.agent_agent RENAME COLUMN business_id TO client_id';
    END IF;
END $$;
"""

REVERSE_SQL = r"""
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = 'agent_agent' AND column_name = 'client_id'
    ) AND NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = 'agent_agent' AND column_name = 'business_id'
    ) THEN
        EXECUTE 'ALTER TABLE public.agent_agent RENAME COLUMN client_id TO business_id';
    END IF;
END $$;
"""

class Migration(migrations.Migration):

    dependencies = [
        ('agent', '0004_initial'),
    ]

    operations = [
        migrations.RunSQL(sql=RENAME_SQL, reverse_sql=REVERSE_SQL),
    ]
