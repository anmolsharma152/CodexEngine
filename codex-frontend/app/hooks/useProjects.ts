"use client";

import { useState, useCallback } from "react";
import type { Project } from "../lib/types";

const STORAGE_KEY = "codex_projects";
const DEFAULT_PROJECT: Project = { id: "default", name: "General", timestamp: 0 };

function loadProjects(): Project[] {
  if (typeof window === "undefined") return [DEFAULT_PROJECT];
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw) {
      const parsed = JSON.parse(raw) as Project[];
      if (parsed.some((p) => p.id === "default")) return parsed;
      return [DEFAULT_PROJECT, ...parsed];
    }
  } catch {}
  return [DEFAULT_PROJECT];
}

function saveProjects(projects: Project[]) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(projects));
}

export function useProjects() {
  const [projects, setProjects] = useState<Project[]>(loadProjects);
  const [activeProjectId, setActiveProjectId] = useState("default");

  const createProject = useCallback((name: string) => {
    const project: Project = { id: crypto.randomUUID(), name, timestamp: Date.now() };
    setProjects((prev) => {
      const next = [...prev, project];
      saveProjects(next);
      return next;
    });
    setActiveProjectId(project.id);
  }, []);

  const renameProject = useCallback((id: string, name: string) => {
    setProjects((prev) => {
      const next = prev.map((p) => (p.id === id ? { ...p, name } : p));
      saveProjects(next);
      return next;
    });
  }, []);

  const deleteProject = useCallback((id: string) => {
    setProjects((prev) => {
      const next = prev.filter((p) => p.id !== id);
      saveProjects(next);
      return next;
    });
    if (activeProjectId === id) setActiveProjectId("default");
  }, [activeProjectId]);

  const activeProject = projects.find((p) => p.id === activeProjectId) || DEFAULT_PROJECT;

  return {
    projects,
    activeProjectId,
    activeProject,
    setActiveProjectId,
    createProject,
    renameProject,
    deleteProject,
  };
}
