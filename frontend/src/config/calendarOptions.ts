import type { CalendarOptions } from "@fullcalendar/core/index.js";
import daygridPlugin from "@fullcalendar/daygrid";
import timegridPlugin from "@fullcalendar/timegrid";
import interactionPlugin from "@fullcalendar/interaction";

export const calendarOptions: CalendarOptions = {
  plugins: [daygridPlugin, timegridPlugin, interactionPlugin],
  initialView: "timeGridWeek",
  locale: "de",
  headerToolbar: {
    start: "prev,today,next",
    center: "title",
    end: "timeGridDay,timeGridWeek",
  },
  buttonText: {
    today: "Heute",
    week: "Woche",
    day: "Tag",
  },
  views: {
    week: {
      titleFormat: {
        year: "numeric",
        month: "long",
        day: "2-digit",
        week: "narrow",
      },
      eventTimeFormat: {
        hour: "numeric",
        minute: "2-digit",
        meridiem: "lowercase",
      },
      dayHeaderFormat: {
        weekday: "long",
        day: "2-digit",
        month: "2-digit",
        year: "numeric",
      },
      slotLabelFormat: { hour: "2-digit", minute: "2-digit" },
    },
  },
  weekends: false,
  businessHours: {
    daysOfWeek: [1, 2, 3, 4, 5],
    startTime: "08:00",
    endTime: "20:00",
  },
  slotMinTime: "08:00:00",
  slotMaxTime: "20:00:00",
  slotDuration: "01:00:00",
  allDaySlot: false,
  height: "auto",
  editable: true,
};
