import type {
  EventClickArg,
  EventContentArg,
} from "@fullcalendar/core/index.js";
import FullCalendar from "@fullcalendar/react";
import { useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "./ui/dialog";
import { Clock, Save, Trash } from "lucide-react";
import { Button } from "./ui/button";
import { Label } from "./ui/label";
import { Input } from "./ui/input";
import { calendarOptions } from "@/config/calendarOptions";

const events = [
  {
    title: "Mensch-Comp.Interakt. (119203a) - Teilgruppe 3",
    extendedProps: {
      room: "32",
    },
    start: new Date("2025-06-03T10:00:00"),
    end: new Date("2025-06-03T11:30:00"),
  },
  {
    title: "Mensch-Comp.Interakt. (119203a) - Teilgruppe 2",
    extendedProps: {
      room: "32",
    },
    start: new Date("2025-06-03T10:00:00"),
    end: new Date("2025-06-03T11:30:00"),
  },
  {
    title: "Mensch-Comp.Interakt. (119203a) - Teilgruppe 1",
    extendedProps: {
      room: "32",
    },
    start: new Date("2025-06-03T10:00:00"),
    end: new Date("2025-06-03T11:30:00"),
  },
];

export function Calendar() {
  const [dialogOpen, setDialogOpen] = useState(false);
  const [selectedEvent, setSelectedEvent] = useState<{
    title: string;
    time: string;
    room?: string;
  } | null>(null);

  const handleEventClick = (clickInfo: EventClickArg) => {
    setSelectedEvent({
      title: clickInfo.event.title,
      time: clickInfo.event.start
        ? new Intl.DateTimeFormat("de-DE", {
            hour: "numeric",
            minute: "2-digit",
            day: "2-digit",
            month: "2-digit",
            year: "numeric",
          }).format(clickInfo.event.start)
        : "Unknown time",
      room: clickInfo.event.extendedProps.room,
    });
    setDialogOpen(true);
  };

  function handleFieldChange(field: string, value: string) {
    setSelectedEvent((prev) => (prev ? { ...prev, [field]: value } : prev));
  }

  return (
    <div className="overflow-auto">
      <FullCalendar
        {...calendarOptions}
        eventClick={handleEventClick}
        events={events}
        eventContent={renderContent}
      />
      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent onOpenAutoFocus={(e) => e.preventDefault()}>
          <DialogHeader>
            <DialogTitle>Kurs bearbeiten</DialogTitle>
            <DialogDescription>
              Nimm Änderungen an dem Kurs vor. Klicke auf "Speichern", um die
              Änderungen zu bestätigen.
            </DialogDescription>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="courseName" className="text-right">
                Kursname
              </Label>
              <Input
                id="courseName"
                value={selectedEvent?.title ?? ""}
                onChange={(e) => handleFieldChange("title", e.target.value)}
                className="col-span-3"
              />
            </div>
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="room" className="text-right">
                Raum
              </Label>
              <Input
                id="room"
                value={selectedEvent?.room ?? ""}
                onChange={(e) => handleFieldChange("room", e.target.value)}
                className="col-span-3"
              />
            </div>
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="time" className="text-right">
                Datum/Uhrzeit
              </Label>
              <Input
                id="time"
                value={selectedEvent?.time ?? ""}
                onChange={(e) => handleFieldChange("time", e.target.value)}
                className="col-span-3"
              />
            </div>
          </div>
          <DialogFooter className="flex sm:justify-between">
            <Button variant="destructive">
              <Trash /> <span>Löschen</span>
            </Button>
            <Button>
              <Save /> <span>Übernehmen</span>
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

function renderContent(info: EventContentArg) {
  return (
    <>
      <div className="relative flex h-full gap-2 overflow-hidden">
        <span className="bg-primary-foreground m-[1px] block h-[calc(100%-2px)] w-[2px] rounded-full"></span>
        <div className="flex flex-col text-xs">
          <div>{info.event.extendedProps.room}</div>
          <span>{info.event.title}</span>
          <span className="flex items-center gap-1">
            <Clock size={11} /> {info.timeText}
          </span>
        </div>
      </div>
    </>
  );
}
