import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import api from '../services/api';

const LabAssistantList = () => {
  const [assistants, setAssistants] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchAssistants = async () => {
      try {
        const response = await api.getLabAssistants();
        console.log('API Response:', response.data); // Debug log
        
        // Handle different response formats
        let assistantData = response.data;
        
        // If response has a 'results' key (pagination), use that
        if (assistantData && assistantData.results) {
          assistantData = assistantData.results;
        }
        
        // Make sure it's an array
        if (!Array.isArray(assistantData)) {
          console.error('Expected array but got:', assistantData);
          assistantData = [];
        }
        
        setAssistants(assistantData);
      } catch (err) {
        console.error('Error fetching lab assistants:', err);
        setError('Failed to load lab assistants. Please try again.');
      } finally {
        setLoading(false);
      }
    };

    fetchAssistants();
  }, []);

  const getStatusClass = (status) => {
    switch (status) {
      case 'active':
        return 'status-active';
      case 'pending':
        return 'status-pending';
      case 'inactive':
        return 'status-inactive';
      default:
        return '';
    }
  };

  if (loading) {
    return (
      <div className="lab-assistant-list">
        <h2>Lab Assistants</h2>
        <p style={{ textAlign: 'center', padding: '40px', color: '#666' }}>
          Loading lab assistants...
        </p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="lab-assistant-list">
        <h2>Lab Assistants</h2>
        <div style={{
          backgroundColor: '#ffebee',
          color: '#c62828',
          padding: '20px',
          borderRadius: '8px',
          textAlign: 'center',
          marginTop: '20px'
        }}>
          {error}
        </div>
      </div>
    );
  }

  return (
    <div className="lab-assistant-list">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
        <h2>Lab Assistants</h2>
        <div style={{ color: '#666', fontSize: '1.1em' }}>
          Total: <strong>{assistants.length}</strong> assistant{assistants.length !== 1 ? 's' : ''}
        </div>
      </div>

      {assistants.length === 0 ? (
        <div style={{
          backgroundColor: '#e3f2fd',
          padding: '30px',
          borderRadius: '8px',
          textAlign: 'center',
          color: '#1976d2'
        }}>
          <p style={{ fontSize: '1.1em', marginBottom: '10px' }}>
            No lab assistants found.
          </p>
          <p style={{ fontSize: '0.95em', opacity: 0.8 }}>
            Lab assistants will appear here once they are added to the system.
          </p>
        </div>
      ) : (
        <div className="assistant-grid">
          {assistants.map((assistant) => (
            <div key={assistant.id} className="assistant-card">
              <h3>
                {assistant.user.first_name} {assistant.user.last_name}
              </h3>
              
              <div style={{ marginBottom: '12px' }}>
                <span className={`assistant-status ${getStatusClass(assistant.status)}`}>
                  {assistant.status}
                </span>
              </div>

              <div style={{ fontSize: '0.9em', color: '#666', marginBottom: '8px' }}>
                <strong>Email:</strong> {assistant.user.email || 'Not provided'}
              </div>

              <div style={{ fontSize: '0.9em', color: '#666', marginBottom: '15px' }}>
                <strong>Username:</strong> {assistant.user.username}
              </div>

              <Link
                to={`/calendar?assistant=${assistant.id}`}
                style={{
                  display: 'inline-block',
                  backgroundColor: '#990000',
                  color: 'white',
                  padding: '8px 16px',
                  borderRadius: '4px',
                  textDecoration: 'none',
                  fontSize: '0.9em',
                  fontWeight: '600',
                  transition: 'background-color 0.3s'
                }}
                onMouseOver={(e) => e.target.style.backgroundColor = '#cc0000'}
                onMouseOut={(e) => e.target.style.backgroundColor = '#990000'}
              >
                View Availability
              </Link>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default LabAssistantList;