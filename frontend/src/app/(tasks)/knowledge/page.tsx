// SPDX-FileCopyrightText: 2025 Weibo, Inc.
//
// SPDX-License-Identifier: Apache-2.0

'use client'

import { useState, useEffect, useCallback } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import TopNavigation from '@/features/layout/TopNavigation'
import {
  TaskSidebar,
  ResizableSidebar,
  CollapsedSidebarButtons,
} from '@/features/tasks/components/sidebar'
import '@/app/tasks/tasks.css'
import '@/features/common/scrollbar.css'
import { GithubStarButton } from '@/features/layout/GithubStarButton'
import { ThemeToggle } from '@/features/theme/ThemeToggle'
import { useTranslation } from '@/hooks/useTranslation'
import { saveLastTab } from '@/utils/userPreferences'
import { useUser } from '@/features/common/UserContext'
import { useIsMobile } from '@/features/layout/hooks/useMediaQuery'
import { useChatStreamContext } from '@/features/tasks/contexts/chatStreamContext'
import { useTaskContext } from '@/features/tasks/contexts/taskContext'
import { paths } from '@/config/paths'
import {
  WikiProjectList,
  AddRepoModal,
  useWikiProjects,
  CancelConfirmDialog,
  SearchBox,
  KnowledgeTabs,
  KnowledgeTabType,
  KnowledgeDocumentPage,
  DocumentTabType,
} from '@/features/knowledge'

export default function KnowledgePage() {
  const { t } = useTranslation()
  const router = useRouter()
  const searchParams = useSearchParams()
  const { user } = useUser()
  const { clearAllStreams } = useChatStreamContext()
  const { setSelectedTask } = useTaskContext()
  const isMobile = useIsMobile()

  // Use shared Hook to manage all state and logic
  const {
    projects,
    loading,
    loadingMore,
    error,
    cancellingIds,
    hasMore,
    isModalOpen,
    formErrors,
    isSubmitting,
    confirmDialogOpen,
    selectedRepo,
    // Wiki config state (system-level configuration)
    wikiConfig,
    loadProjects,
    loadMoreProjects,
    handleAddRepo,
    handleCloseModal,
    handleRepoChange,
    handleSubmit,
    handleCancelClick,
    confirmCancelGeneration,
    setConfirmDialogOpen,
    setPendingCancelProjectId,
  } = useWikiProjects()

  // Read URL parameters for initial state
  const typeParam = searchParams.get('type') as KnowledgeTabType | null
  const tabParam = searchParams.get('tab') as DocumentTabType | null
  const groupParam = searchParams.get('group')

  // Active knowledge tab - initialize from URL param 'type'
  const [activeTab, setActiveTab] = useState<KnowledgeTabType>(() => {
    if (typeParam === 'code' || typeParam === 'document') {
      return typeParam
    }
    return 'document'
  })

  // Document sub-tab state - managed by KnowledgeDocumentPage but controlled here
  const [documentTab, setDocumentTab] = useState<DocumentTabType>(() => {
    if (tabParam === 'personal' || tabParam === 'group' || tabParam === 'external') {
      return tabParam
    }
    return 'personal'
  })

  // Selected group state
  const [selectedGroup, setSelectedGroup] = useState<string | null>(groupParam)

  // Search term for project list
  const [mainSearchTerm, setMainSearchTerm] = useState('')

  // Mobile sidebar state
  const [isMobileSidebarOpen, setIsMobileSidebarOpen] = useState(false)

  // Collapsed sidebar state
  const [isCollapsed, setIsCollapsed] = useState(false)

  // Update URL when state changes
  const updateUrl = useCallback(
    (type: KnowledgeTabType, tab?: DocumentTabType | null, group?: string | null) => {
      const params = new URLSearchParams()

      // Always set type
      params.set('type', type)

      // Only set tab for document type
      if (type === 'document' && tab) {
        params.set('tab', tab)
      }

      // Only set group when on group tab and group is selected
      if (type === 'document' && tab === 'group' && group) {
        params.set('group', group)
      }

      const newUrl = `/knowledge?${params.toString()}`
      router.replace(newUrl)
    },
    [router]
  )

  // Handle knowledge type tab change
  const handleKnowledgeTabChange = useCallback(
    (tab: KnowledgeTabType) => {
      setActiveTab(tab)
      if (tab === 'code') {
        updateUrl(tab)
      } else {
        // When switching to document, preserve current document tab but clear group
        updateUrl(tab, documentTab, null)
        setSelectedGroup(null)
      }
    },
    [documentTab, updateUrl]
  )

  // Handle document sub-tab change
  const handleDocumentTabChange = useCallback(
    (tab: DocumentTabType) => {
      setDocumentTab(tab)
      // Clear group when switching document tabs
      setSelectedGroup(null)
      updateUrl('document', tab, null)
    },
    [updateUrl]
  )

  // Handle group selection/deselection
  const handleGroupChange = useCallback(
    (groupName: string | null) => {
      setSelectedGroup(groupName)
      updateUrl('document', 'group', groupName)
    },
    [updateUrl]
  )

  const navigateToKnowledgeDetail = (projectId: number) => {
    router.push(`/knowledge/${projectId}`)
  }

  const navigateToTask = (taskId: number) => {
    router.push(`/code?taskId=${taskId}`)
  }

  // Filter projects to show only those with user's generations
  // This ensures the knowledge page only shows projects created by the current user
  const userProjects = projects.filter(project => {
    // Check if user has any generations for this project
    return (
      project.generations &&
      project.generations.length > 0 &&
      (project.generations[0].status === 'RUNNING' ||
        project.generations[0].status === 'COMPLETED' ||
        project.generations[0].status === 'PENDING' ||
        project.generations[0].status === 'FAILED' ||
        project.generations[0].status === 'CANCELLED')
    )
  })

  // Load collapsed state from localStorage
  useEffect(() => {
    const savedCollapsed = localStorage.getItem('task-sidebar-collapsed')
    if (savedCollapsed === 'true') {
      setIsCollapsed(true)
    }
  }, [])

  useEffect(() => {
    saveLastTab('wiki')
  }, [])

  useEffect(() => {
    if (!user) return
    loadProjects()
  }, [user, loadProjects])

  const handleToggleCollapsed = () => {
    setIsCollapsed(prev => {
      const newValue = !prev
      localStorage.setItem('task-sidebar-collapsed', String(newValue))
      return newValue
    })
  }

  // Handle new task from collapsed sidebar button
  const handleNewTask = () => {
    // IMPORTANT: Clear selected task FIRST to ensure UI state is reset immediately
    // This prevents the UI from being stuck showing the previous task's messages
    setSelectedTask(null)
    clearAllStreams()
    router.replace(paths.chat.getHref())
  }

  return (
    <div className="flex smart-h-screen bg-base text-text-primary box-border">
      {/* Collapsed sidebar floating buttons */}
      {isCollapsed && !isMobile && (
        <CollapsedSidebarButtons onExpand={handleToggleCollapsed} onNewTask={handleNewTask} />
      )}

      {/* Responsive resizable sidebar */}
      <ResizableSidebar isCollapsed={isCollapsed} onToggleCollapsed={handleToggleCollapsed}>
        <TaskSidebar
          isMobileSidebarOpen={isMobileSidebarOpen}
          setIsMobileSidebarOpen={setIsMobileSidebarOpen}
          pageType="knowledge"
          isCollapsed={isCollapsed}
          onToggleCollapsed={handleToggleCollapsed}
        />
      </ResizableSidebar>

      {/* Main content area */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Top navigation */}
        <TopNavigation
          activePage="wiki"
          variant="with-sidebar"
          title={t('knowledge:title')}
          onMobileSidebarToggle={() => setIsMobileSidebarOpen(true)}
          isSidebarCollapsed={isCollapsed}
        >
          {isMobile ? <ThemeToggle /> : <GithubStarButton />}
        </TopNavigation>

        {/* Knowledge type tabs */}
        <KnowledgeTabs activeTab={activeTab} onTabChange={handleKnowledgeTabChange} />

        {/* Content area based on active tab */}
        <div className="flex-1 overflow-auto p-6">
          {activeTab === 'code' && (
            <>
              {/* Center search box - using shared component */}
              <SearchBox
                value={mainSearchTerm}
                onChange={setMainSearchTerm}
                placeholder={t('knowledge:search_repositories')}
                size="md"
                className="mb-6 max-w-2xl mx-auto"
              />
              {/* Project list */}
              <WikiProjectList
                projects={userProjects}
                loading={loading}
                loadingMore={loadingMore}
                error={error}
                onAddRepo={handleAddRepo}
                onProjectClick={navigateToKnowledgeDetail}
                onTaskClick={navigateToTask}
                onCancelClick={handleCancelClick}
                cancellingIds={cancellingIds}
                searchTerm={mainSearchTerm}
                hasMore={hasMore}
                onLoadMore={loadMoreProjects}
                currentUserId={user?.id}
              />
            </>
          )}

          {activeTab === 'document' && (
            <KnowledgeDocumentPage
              initialTab={documentTab}
              initialGroup={selectedGroup ?? undefined}
              onTabChange={handleDocumentTabChange}
              onGroupChange={handleGroupChange}
            />
          )}
        </div>
      </div>

      {/* Add repository modal */}
      <AddRepoModal
        isOpen={isModalOpen}
        onClose={handleCloseModal}
        formErrors={formErrors}
        isSubmitting={isSubmitting}
        onRepoChange={handleRepoChange}
        onSubmit={handleSubmit}
        selectedRepo={selectedRepo}
        wikiConfig={wikiConfig}
      />
      {/* Cancel confirm dialog */}
      <CancelConfirmDialog
        isOpen={confirmDialogOpen}
        onClose={() => {
          setConfirmDialogOpen(false)
          setPendingCancelProjectId(null)
        }}
        onConfirm={confirmCancelGeneration}
      />
    </div>
  )
}
