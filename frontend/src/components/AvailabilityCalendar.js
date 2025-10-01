import React, { useState, useEffect } from 'react';
import { Calendar, momentLocalizer } from 'react-big-calendar';
import moment from 'moment';
import 'react-big-calendar/lib/css/react-big-calendar.css';
import api from '../services/api';
import './AvailabilityCalendar.css';

const localizer = momentLocalizer(moment);

const AvailabilityCalendar = ({ labAssistantId = null }) => {
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [labAssistants, setLabAssistants] = useState([]);
  const [selectedAssistant, setSelectedAssistant] = useState(labAssistantId);
  const [currentDate, setCurrentDate] = useState(new Date());
  const [currentView, setCurrentView] = useState('week');

  // Fetch lab assistants for the filter dropdown
  useEffect(() => {
    const fetchLabAssistants = async () => {
      try {
        const response = await api.getLabAssistants();
        console.log('Lab Assistants Response:', response.data);
        
        let assistantData = response.data;
        
        if (assistantData && assistantData.results) {
          assistantData = assistantData.results;
        }
        
        if (!Array.isArray(assistantData)) {
          assistantData = [];
        }
        
        setLabAssistants(assistantData);
      } catch (err) {
        console.error('Error fetching lab assistants:', err);
      }
    };
    fetchLabAssistants();
  }, []);

  // Fetch and process availability data
  useEffect(() => {
    const fetchAvailability = async () => {
      setLoading(true);
      setError(null);
      
      try {
        let response;
        if (selectedAssistant) {
          response = await api.getAvailability({ lab_assistant: selectedAssistant });
        } else {
          response = await api.getAvailability();
        }

        console.log('Availability Response:', response.data);
        
        let availabilityData = response.data;
        
        if (availabilityData && availabilityData.results) {
          availabilityData = availabilityData.results;
        }
        
        if (!Array.isArray(availabilityData)) {
          availabilityData = [];
        }

        const calendarEvents = convertToCalendarEvents(availabilityData);
        setEvents(calendarEvents);
      } catch (err) {
        console.error('Error fetching availability:', err);
        setError('Failed to load availability data. Please try again.');
      } finally {
        setLoading(false);
      }
    };

    fetchAvailability();
  }, [selectedAssistant, currentDate]);

  const convertToCalendarEvents = (availabilityData) => {
    const events = [];
    const startOfWeek = moment(currentDate).startOf('week');

    availabilityData.forEach((availability) => {
      const eventDate = startOfWeek.clone().add(availability.day_of_week, 'days');
      
      const [startHour, startMinute] = availability.start_time.split(':').map(Number);
      const [endHour, endMinute] = availability.end_time.split(':').map(Number);

      const startDateTime = eventDate.clone().set({
        hour: startHour,
        minute: startMinute,
        second: 0
      });

      const endDateTime = eventDate.clone().set({
        hour: endHour,
        minute: endMinute,
        second: 0
      });

      events.push({
        id: availability.id,
        title: availability.lab_assistant_name || 'Available',
        start: startDateTime.toDate(),
        end: endDateTime.toDate(),
        resource: {
          labAssistantId: availability.lab_assistant,
          labAssistantName: availability.lab_assistant_name,
          dayOfWeek: availability.day_of_week,
          dayDisplay: availability.day_of_week_display
        }
      });
    });

    return events;
  };

  const eventStyleGetter = (event) => {
    const backgroundColor = selectedAssistant ? '#4CAF50' : '#2196F3';
    
    return {
      style: {
        backgroundColor,
        borderRadius: '5px',
        opacity: 0.8,
        color: 'white',
        border: '0px',
        display: 'block',
        fontSize: '0.9em',
        padding: '2px 5px'
      }
    };
  };

  const EventComponent = ({ event }) => (
    <div style={{ fontSize: '0.85em' }}>
      <strong>{event.resource.labAssistantName}</strong>
      <div style={{ fontSize: '0.9em' }}>
        {moment(event.start).format('h:mm A')} - {moment(event.end).format('h:mm A')}
      </div>
    </div>
  );

  const handleNavigate = (newDate) => {
    setCurrentDate(newDate);
  };

  const handleViewChange = (newView) => {
    setCurrentView(newView);
  };

  if (loading) {
    return (
      <div className="calendar-container">
        <div className="loading-spinner">Loading availability data...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="calendar-container">
        <div className="error-message">{error}</div>
      </div>
    );
  }

  return (
    <div className="calendar-container">
      <div className="calendar-header">
        <h2>Lab Assistant Availability Calendar</h2>
        
        <div className="calendar-controls">
          <label htmlFor="assistant-filter">Filter by Assistant: </label>
          <select
            id="assistant-filter"
            value={selectedAssistant || ''}
            onChange={(e) => setSelectedAssistant(e.target.value || null)}
            className="assistant-select"
          >
            <option value="">All Assistants</option>
            {labAssistants.map((assistant) => (
              <option key={assistant.id} value={assistant.id}>
                {assistant.user.first_name} {assistant.user.last_name}
              </option>
            ))}
          </select>
        </div>
      </div>

      <div className="calendar-info">
        <p>
          Showing {events.length} availability block{events.length !== 1 ? 's' : ''}
          {selectedAssistant && ' for selected assistant'}
        </p>
      </div>

      <Calendar
        localizer={localizer}
        events={events}
        startAccessor="start"
        endAccessor="end"
        style={{ height: 600 }}
        view={currentView}
        onView={handleViewChange}
        date={currentDate}
        onNavigate={handleNavigate}
        views={['week', 'day']}
        step={30}
        timeslots={2}
        eventPropGetter={eventStyleGetter}
        components={{
          event: EventComponent
        }}
        min={moment().set({ hour: 8, minute: 0 }).toDate()}
        max={moment().set({ hour: 20, minute: 0 }).toDate()}
      />

      <div className="calendar-legend">
        <h4>Legend:</h4>
        <div className="legend-item">
          <span className="legend-color" style={{ backgroundColor: selectedAssistant ? '#4CAF50' : '#2196F3' }}></span>
          <span>Available for assignment</span>
        </div>
      </div>
    </div>
  );
};

export default AvailabilityCalendar;