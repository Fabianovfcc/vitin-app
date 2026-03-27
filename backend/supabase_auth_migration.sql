-- Migração para Autenticação Segura (Celular, PIN e Biometria)
-- Executar no SQL Editor do Supabase

-- 1. Alterar tabela students para incluir campos de autenticação
ALTER TABLE students 
ADD COLUMN IF NOT EXISTS phone_auth TEXT UNIQUE,
ADD COLUMN IF NOT EXISTS pin_hash TEXT,
ADD COLUMN IF NOT EXISTS webauthn_credential JSONB;

-- 2. Criar índice para performance em logins recorrentes
CREATE INDEX IF NOT EXISTS idx_students_phone_auth ON students(phone_auth);

-- 3. (Opcional) Migrar whatsapp atual para phone_auth onde disponível
-- UPDATE students SET phone_auth = whatsapp WHERE phone_auth IS NULL AND whatsapp IS NOT NULL;
