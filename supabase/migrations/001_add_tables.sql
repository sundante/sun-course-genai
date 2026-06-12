-- Migration 001: Add interactive feature tables
-- Run in Supabase SQL Editor after setup.sql

-- ── user_progress ─────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.user_progress (
  id           UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id      UUID        NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  module       TEXT        NOT NULL,  -- e.g. "llm-models"
  slug         TEXT        NOT NULL,  -- e.g. "01-llm-fundamentals"
  completed    BOOLEAN     DEFAULT false,
  completed_at TIMESTAMPTZ,
  created_at   TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(user_id, module, slug)
);

ALTER TABLE public.user_progress ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users own their progress"
  ON public.user_progress FOR ALL
  USING (auth.uid() = user_id);

-- ── quiz_sessions ─────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.quiz_sessions (
  id          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id     UUID        REFERENCES auth.users(id) ON DELETE SET NULL,
  module      TEXT,                    -- null = all-modules shuffle
  total       INTEGER     NOT NULL,
  correct     INTEGER     NOT NULL,
  duration_s  INTEGER,
  created_at  TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE public.quiz_sessions ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users own their quiz sessions"
  ON public.quiz_sessions FOR ALL
  USING (auth.uid() = user_id);

-- ── subscribers ───────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.subscribers (
  id            UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  email         TEXT        UNIQUE NOT NULL,
  name          TEXT,
  subscribed_at TIMESTAMPTZ DEFAULT NOW(),
  source        TEXT        -- 'homepage', 'module-footer', etc.
);

-- No RLS on subscribers - inserts happen unauthenticated (email capture)

-- ── page_feedback ─────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.page_feedback (
  id         UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id    UUID        REFERENCES auth.users(id) ON DELETE SET NULL,
  page_slug  TEXT        NOT NULL,
  vote       TEXT        CHECK (vote IN ('up', 'down')),
  created_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(user_id, page_slug)
);

ALTER TABLE public.page_feedback ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Anyone can insert feedback"
  ON public.page_feedback FOR INSERT WITH CHECK (true);

CREATE POLICY "Users see own feedback"
  ON public.page_feedback FOR SELECT USING (auth.uid() = user_id);

-- ── subscriptions ─────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.subscriptions (
  id                     UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id                UUID        UNIQUE NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  stripe_customer_id     TEXT        UNIQUE,
  stripe_subscription_id TEXT        UNIQUE,
  plan                   TEXT        NOT NULL DEFAULT 'free',   -- 'free' | 'pro' | 'cohort'
  status                 TEXT        NOT NULL DEFAULT 'active', -- 'active' | 'canceled' | 'past_due'
  current_period_end     TIMESTAMPTZ,
  created_at             TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE public.subscriptions ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users view own subscription"
  ON public.subscriptions FOR SELECT USING (auth.uid() = user_id);

-- ── Update handle_new_user to auto-create free subscription ───────────────
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

  -- Auto-create free tier subscription
  INSERT INTO public.subscriptions (user_id, plan, status)
  VALUES (NEW.id, 'free', 'active')
  ON CONFLICT (user_id) DO NOTHING;

  RETURN NEW;
END;
$$;
