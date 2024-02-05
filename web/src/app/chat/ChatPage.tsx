"use client";

import { useState } from "react";
import { FiMenu } from "react-icons/fi";
import { useSearchParams } from "next/navigation";
import { ChatSession } from "./interfaces";
import { ChatSidebar } from "./sessionSidebar/ChatSidebar";
import { Chat } from "./Chat";
import { DocumentSet, Tag, User, ValidSources } from "@/lib/types";
import { Persona } from "../admin/personas/interfaces";
import { Header } from "@/components/Header";
import { HealthCheckBanner } from "@/components/health/healthcheck";
import { ApiKeyModal } from "@/components/openai/ApiKeyModal";
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
          className="md:hidden p-4"
          onClick={() => setIsSidebarOpen(!isSidebarOpen)}
        >
          <FiMenu />
        </button>
      </div>
      <HealthCheckBanner />
      <ApiKeyModal />
      <InstantSSRAutoRefresh />

      <div className="flex relative bg-background text-default overflow-x-hidden">
        <div
          className={`transform top-0 left-0 w-full md:w-96 fixed h-full overflow-auto ease-in-out transition-all duration-300 z-30 ${
            isSidebarOpen ? "translate-x-0" : "-translate-x-full"
          } md:translate-x-0 md:relative md:static bg-background`}
        >
          <ChatSidebar
            existingChats={chatSessions}
            currentChatId={chatId}
            user={user}
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
