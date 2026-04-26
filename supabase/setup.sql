-- GenAI Curriculum — Supabase setup
-- Run this once in the Supabase SQL Editor (https://app.supabase.com → SQL Editor)

-- ── profiles table ────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.profiles (
  id              UUID        PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  name            TEXT,
  role            TEXT,
  profession      TEXT,
  background_type TEXT,
  age_range       TEXT,
  topics          TEXT,        -- comma-separated: "LLMs,RAGs,Agents"
  city            TEXT,
  country         TEXT,
  course_name     TEXT,
  created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ── Row Level Security ────────────────────────────────────────────────────
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own profile"
  ON public.profiles FOR SELECT
  USING (auth.uid() = id);

CREATE POLICY "Users can update own profile"
  ON public.profiles FOR UPDATE
  USING (auth.uid() = id);

-- ── Trigger: auto-create profile on sign-up ───────────────────────────────
-- Reads metadata passed via signInWithOtp options.data and writes a profile row.
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
BEGIN
  INSERT INTO public.profiles (
    id, name, role, profession, background_type,
    age_range, topics, city, country, course_name
  )
  VALUES (
    NEW.id,
    NEW.raw_user_meta_data->>'name',
    NEW.raw_user_meta_data->>'role',
    NEW.raw_user_meta_data->>'profession',
    NEW.raw_user_meta_data->>'background_type',
    NEW.raw_user_meta_data->>'age_range',
    NEW.raw_user_meta_data->>'topics',
    NEW.raw_user_meta_data->>'city',
    NEW.raw_user_meta_data->>'country',
    NEW.raw_user_meta_data->>'course_name'
  )
  ON CONFLICT (id) DO NOTHING;
  RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();
