from fastapi import APIRouter, HTTPException
from models.schemas import GoogleAnalyticsRequest
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import RunReportRequest, DateRange, Metric
from google.analytics.data_v1beta.types import Dimension

import tempfile
import json
import os

router = APIRouter()

@router.post("/api/projects/{project_id}/google-analytics/fetch")
def fetch_google_analytics_data(project_id: int, request: GoogleAnalyticsRequest):
    try:
        # Save the service account json to a temp file
        with tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix='.json') as f:
            json.dump(request.service_account_json, f)
            f.flush()
            credentials_path = f.name

            client = BetaAnalyticsDataClient.from_service_account_file(credentials_path)
            
        # Clean up the temp file after client initialization
        os.unlink(credentials_path)
        
        # Prepare the request
        ga_request = RunReportRequest(
            property=f"properties/{request.property_id}",
            date_ranges=[DateRange(start_date=request.start_date, end_date=request.end_date)],
            metrics=[Metric(name=m) for m in request.metrics],
        )

        response = client.run_report(ga_request)

        result = {
            "dimension_headers": [header.name for header in response.dimension_headers],
            "metric_headers": [header.name for header in response.metric_headers],
            "rows": [
                {
                    "dimensions": [v.value for v in row.dimension_values],
                    "metrics": [v.value for v in row.metric_values]
                }
                for row in response.rows
            ]
        }

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch Google Analytics data: {str(e)}")
