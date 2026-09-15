-- Chạy trong Supabase Dashboard > SQL Editor để tạo bảng lưu kết quả.

create table if not exists public.exam_results (
    id bigint generated always as identity primary key,
    created_at timestamptz not null default now(),
    device_id text,
    exam_id text,
    exam_name text,
    percent int,
    correct int,
    total int,
    answered int,
    time_used int,
    answers jsonb
);

create index if not exists exam_results_lookup on public.exam_results (
    device_id,
    exam_id,
    created_at desc
);

-- Bật Row Level Security và cho phép client (anon) đọc/ghi.
alter table public.exam_results enable row level security;

drop policy if exists "anon read" on public.exam_results;

drop policy if exists "anon insert" on public.exam_results;

drop policy if exists "anon delete" on public.exam_results;

create policy "anon read" on public.exam_results for
select to anon using (true);

create policy "anon insert" on public.exam_results for insert to anon
with
    check (true);

create policy "anon delete" on public.exam_results for delete to anon using (true);