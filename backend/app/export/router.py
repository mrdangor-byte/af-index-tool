import csv
import io
import zipfile

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.user import User
from ..models.project import Project
from ..models.result import AnalysisResult
from ..auth.router import get_current_user

router = APIRouter()


def _get_user_project(project_id: int, db: Session, current_user: User) -> Project:
    project = db.query(Project).filter(
        Project.id == project_id, Project.user_id == current_user.id
    ).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.get("/projects/{project_id}/export/csv")
def export_csv(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = _get_user_project(project_id, db, current_user)
    result = db.query(AnalysisResult).filter(
        AnalysisResult.project_id == project_id
    ).first()
    if not result:
        raise HTTPException(status_code=404, detail="No results found. Run analysis first.")

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        # Headline results
        headline_buf = io.StringIO()
        writer = csv.writer(headline_buf)
        writer.writerow(["Metric", "Value"])
        writer.writerow(["H (Headcount Ratio)", result.H])
        writer.writerow(["A (Average Intensity)", result.A])
        writer.writerow(["M0 (Adjusted Headcount)", result.M0])
        writer.writerow(["q (Identified Poor)", result.q])
        writer.writerow(["n (Total Observations)", result.n])
        zf.writestr("headline_results.csv", headline_buf.getvalue())

        # Dimensional breakdown
        if result.dimensional_breakdown:
            dim_buf = io.StringIO()
            writer = csv.DictWriter(dim_buf, fieldnames=result.dimensional_breakdown[0].keys())
            writer.writeheader()
            writer.writerows(result.dimensional_breakdown)
            zf.writestr("dimensional_breakdown.csv", dim_buf.getvalue())

        # Subgroup decomposition
        if result.subgroup_decomposition:
            sub_buf = io.StringIO()
            writer = csv.DictWriter(sub_buf, fieldnames=result.subgroup_decomposition[0].keys())
            writer.writeheader()
            writer.writerows(result.subgroup_decomposition)
            zf.writestr("subgroup_decomposition.csv", sub_buf.getvalue())

        # Robustness results
        if result.robustness_results:
            rob = result.robustness_results
            if rob.get("k_robustness"):
                k_buf = io.StringIO()
                writer = csv.DictWriter(k_buf, fieldnames=rob["k_robustness"][0].keys())
                writer.writeheader()
                writer.writerows(rob["k_robustness"])
                zf.writestr("k_robustness.csv", k_buf.getvalue())

            if rob.get("leave_one_out"):
                loo_buf = io.StringIO()
                writer = csv.DictWriter(loo_buf, fieldnames=rob["leave_one_out"][0].keys())
                writer.writeheader()
                writer.writerows(rob["leave_one_out"])
                zf.writestr("leave_one_out.csv", loo_buf.getvalue())

    zip_buffer.seek(0)
    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename={project.name}_results.zip"},
    )


@router.get("/projects/{project_id}/export/pdf")
def export_pdf(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = _get_user_project(project_id, db, current_user)
    result = db.query(AnalysisResult).filter(
        AnalysisResult.project_id == project_id
    ).first()
    if not result:
        raise HTTPException(status_code=404, detail="No results found. Run analysis first.")

    # Placeholder: return JSON summary instead of PDF for now
    return {
        "message": "PDF export coming soon",
        "project_name": project.name,
        "headline": {
            "H": result.H,
            "A": result.A,
            "M0": result.M0,
            "q": result.q,
            "n": result.n,
        },
        "dimensional_breakdown": result.dimensional_breakdown,
        "subgroup_decomposition": result.subgroup_decomposition,
    }
