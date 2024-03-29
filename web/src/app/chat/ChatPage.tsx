"use client";

import { Header } from "@/components/Header";
import { HealthCheckBanner } from "@/components/health/healthcheck";
import { ApiKeyModal } from "@/components/openai/ApiKeyModal";
import { DocumentSet, Tag, User, ValidSources } from "@/lib/types";
import { useSearchParams } from "next/navigation";
import { useState } from "react";
import { FiMenu, FiX } from "react-icons/fi";
import { Persona } from "../admin/personas/interfaces";
import { Chat } from "./Chat";
import { ChatSession } from "./interfaces";
import { ChatSidebar } from "./sessionSidebar/ChatSidebar";
import { InstantSSRAutoRefresh } from "@/components/SSRAutoRefresh";

export function ChatLayout({
  user,
  chatSessions,
  availableSources,
  availableDocumentSets,
  availablePersonas,
  availableTags,
  defaultSelectedPersonaId,
  documentSidebarInitialWidth,
}: {
  user: User | null;
  chatSessions: ChatSession[];
  availableSources: ValidSources[];
  availableDocumentSets: DocumentSet[];
  availablePersonas: Persona[];
  availableTags: Tag[];
  defaultSelectedPersonaId?: number; // what persona to default to
  documentSidebarInitialWidth?: number;
}) {
  const searchParams = useSearchParams();
  const chatIdRaw = searchParams.get("chatId");
  const chatId = chatIdRaw ? parseInt(chatIdRaw) : null;
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);

  const selectedChatSession = chatSessions.find(
    (chatSession) => chatSession.id === chatId
  );

  return (
    <>
      <div className="absolute top-0 z-40 w-full">
        <Header user={user} />
        <button
          className={`md:hidden p-4 ${isSidebarOpen ? "bg-gray-300" : ""}`}
          onClick={() => setIsSidebarOpen(!isSidebarOpen)}
        >
          {isSidebarOpen ? <FiX /> : <FiMenu />}
        </button>
      </div>
      <HealthCheckBanner />
      <InstantSSRAutoRefresh />

      <div className="flex relative bg-background text-default overflow-x-hidden">
        <div
          className={`transform top-0 left-0 w-full md:w-96 fixed h-full overflow-auto ease-in-out transition-all duration-300 z-30 ${
            isSidebarOpen ? "translate-x-0" : "-translate-x-full"
          } md:translate-x-0 md:relative md:static bg-background pt-10 sm:pt-0`}
        >
          <ChatSidebar
            existingChats={chatSessions}
            currentChatSession={selectedChatSession}
            user={user}
            setIsSidebarOpen={setIsSidebarOpen}
          />
        </div>

        <Chat
          existingChatSessionId={chatId}
          existingChatSessionPersonaId={selectedChatSession?.persona_id}
          availableSources={availableSources}
          availableDocumentSets={availableDocumentSets}
          availablePersonas={availablePersonas}
          availableTags={availableTags}
          defaultSelectedPersonaId={defaultSelectedPersonaId}
          documentSidebarInitialWidth={documentSidebarInitialWidth}
        />
      </div>
    </>
  );
}
