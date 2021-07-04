--
-- PostgreSQL database dump
--

-- Dumped from database version 10.17
-- Dumped by pg_dump version 10.17

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_with_oids = false;

--
-- Name: films; Type: TABLE; Schema: public; Owner: postgres
--

/*
Purpose:
An example of a table dumped with pg_dump.
*/

CREATE TABLE public.films (
    code character(5) NOT NULL,
    title character varying(40) NOT NULL
);


ALTER TABLE public.films OWNER TO postgres;

--
-- Name: TABLE films; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON TABLE public.films IS 'These are my favorite films';


--
-- Name: COLUMN films.code; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.films.code IS 'This is the IMDB identification';


--
-- Name: COLUMN films.title; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.films.title IS 'Original title';


--
-- Name: films firstkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.films
    ADD CONSTRAINT firstkey PRIMARY KEY (code);


--
-- PostgreSQL database dump complete
--

