import { supabase } from "./supabase";
import type { Project } from "./store";

/**
 * Fetch projects for the currently logged-in user directly from Supabase
 * This leverages Supabase RLS policies and returns only the user's projects
 */
export async function fetchProjectsForUser(): Promise<Project[]> {
  // Get current user
  const { data: userData, error: userError } = await supabase.auth.getUser();
  
  if (userError || !userData?.user) {
    console.error("Unable to get current user:", userError);
    throw new Error("Unable to get current user");
  }

  console.log("Fetching projects for user:", userData.user.id);

  // Fetch projects for the user
  const { data: projects, error } = await supabase
    .from("projects")
    .select("*")
    .eq("user_id", userData.user.id)  // Filter by user_id
    .order("created_at", { ascending: false });

  if (error) {
    console.error("Failed to fetch projects:", error);
    return [];
  }

  // Convert to our Project interface format
  return (projects || []).map(project => ({
    id: project.id.toString(),
    name: project.name,
    persona: project.persona,
    context: project.context,
    industry: project.industry,
    createdAt: project.created_at,
    user_id: project.user_id
  }));
}
