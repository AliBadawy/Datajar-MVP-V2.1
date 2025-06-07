-- Create policy to allow inserting data into the google_analytics_data table
CREATE POLICY google_analytics_data_insert_policy 
    ON public.google_analytics_data 
    FOR INSERT
    WITH CHECK (true);
    
-- Note: This is a permissive policy that allows any authenticated user to insert data
-- For production use, you should restrict this to appropriate users/roles
-- Example of a more restrictive policy:
-- WITH CHECK (auth.uid() = (SELECT user_id FROM public.projects WHERE id = google_analytics_data.project_id));
