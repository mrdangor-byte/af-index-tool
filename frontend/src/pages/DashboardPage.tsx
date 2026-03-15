import { useState, useEffect } from 'react';
import type { FormEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import api from '../api/client';
import type { Project } from '../types';

export default function DashboardPage() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showModal, setShowModal] = useState(false);
  const [newName, setNewName] = useState('');
  const [newDesc, setNewDesc] = useState('');
  const [creating, setCreating] = useState(false);

  const fetchProjects = async () => {
    try {
      const res = await api.get('/projects');
      setProjects(res.data);
    } catch {
      setError('Failed to load projects');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProjects();
  }, []);

  const handleCreate = async (e: FormEvent) => {
    e.preventDefault();
    setCreating(true);
    try {
      const res = await api.post('/projects', {
        name: newName,
        description: newDesc || undefined,
      });
      setShowModal(false);
      setNewName('');
      setNewDesc('');
      navigate(`/projects/${res.data.id}`);
    } catch {
      setError('Failed to create project');
    } finally {
      setCreating(false);
    }
  };

  const statusLabel = (status: string) => {
    const labels: Record<string, string> = {
      draft: 'Draft',
      configured: 'Configured',
      analyzed: 'Analyzed',
      complete: 'Complete',
    };
    return labels[status] || status;
  };

  return (
    <div className="dashboard-page">
      <header className="dashboard-header">
        <div className="header-left">
          <h1>AF Index Tool</h1>
        </div>
        <div className="header-right">
          <span className="user-name">{user?.full_name}</span>
          <button className="btn btn-secondary btn-sm" onClick={logout}>
            Log Out
          </button>
        </div>
      </header>

      <main className="dashboard-main">
        <div className="dashboard-title-row">
          <h2>Your Projects</h2>
          <button className="btn btn-primary" onClick={() => setShowModal(true)}>
            + New Project
          </button>
        </div>

        {error && <div className="error-message">{error}</div>}

        {loading ? (
          <div className="loading">Loading projects...</div>
        ) : projects.length === 0 ? (
          <div className="empty-state">
            <p>You have no projects yet. Create one to get started.</p>
          </div>
        ) : (
          <div className="project-grid">
            {projects.map((project) => (
              <div
                key={project.id}
                className="project-card"
                onClick={() => navigate(`/projects/${project.id}`)}
              >
                <h3>{project.name}</h3>
                {project.description && <p className="project-desc">{project.description}</p>}
                <div className="project-meta">
                  <span className={`status-badge status-${project.status}`}>
                    {statusLabel(project.status)}
                  </span>
                  <span className="project-date">
                    {new Date(project.created_at).toLocaleDateString()}
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </main>

      {showModal && (
        <div className="modal-overlay" onClick={() => setShowModal(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <h3>New Project</h3>
            <form onSubmit={handleCreate}>
              <div className="form-group">
                <label htmlFor="projectName">Project Name</label>
                <input
                  id="projectName"
                  type="text"
                  value={newName}
                  onChange={(e) => setNewName(e.target.value)}
                  required
                  placeholder="e.g., South Africa MPI 2024"
                />
              </div>
              <div className="form-group">
                <label htmlFor="projectDesc">Description (optional)</label>
                <textarea
                  id="projectDesc"
                  value={newDesc}
                  onChange={(e) => setNewDesc(e.target.value)}
                  rows={3}
                  placeholder="Brief description of this analysis..."
                />
              </div>
              <div className="modal-actions">
                <button type="button" className="btn btn-secondary" onClick={() => setShowModal(false)}>
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary" disabled={creating}>
                  {creating ? 'Creating...' : 'Create Project'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
