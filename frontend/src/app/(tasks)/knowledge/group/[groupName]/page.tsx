// SPDX-FileCopyrightText: 2025 Weibo, Inc.
//
// SPDX-License-Identifier: Apache-2.0

'use client'

import { useState, useEffect, useMemo } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { Users, Plus, FileText, ArrowLeft, Search, BookOpen, FolderOpen } from 'lucide-react'
import TopNavigation from '@/features/layout/TopNavigation'
import {
  TaskSidebar,
  ResizableSidebar,
  CollapsedSidebarButtons,
} from '@/features/tasks/components/sidebar'
import { GithubStarButton } from '@/features/layout/GithubStarButton'
import { ThemeToggle } from '@/features/theme/ThemeToggle'
import { Spinner } from '@/components/ui/spinner'
import { Card } from '@/components/ui/card'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown'
import { useTranslation } from '@/hooks/useTranslation'
import { useIsMobile } from '@/features/layout/hooks/useMediaQuery'
import { useChatStreamContext } from '@/features/tasks/contexts/chatStreamContext'
import { useTaskContext } from '@/features/tasks/contexts/taskContext'
import { saveLastTab } from '@/utils/userPreferences'
import { listGroups } from '@/apis/groups'
import { paths } from '@/config/paths'
import {
  KnowledgeBaseCard,
  CreateKnowledgeBaseDialog,
  EditKnowledgeBaseDialog,
  DeleteKnowledgeBaseDialog,
} from '@/features/knowledge/document/components'
import { useKnowledgeBases } from '@/features/knowledge/document/hooks'
import type { Group } from '@/types/group'
import type { KnowledgeBase, KnowledgeBaseType } from '@/types/knowledge'

/**
 * Group Knowledge Base List Page
 *
 * Displays knowledge bases for a specific group.
 * Route: /knowledge/group/[groupName]
 */
export default function GroupKnowledgeBasePage() {
  const { t } = useTranslation()
  const router = useRouter()
  const params = useParams()
  const isMobile = useIsMobile()
  const { clearAllStreams } = useChatStreamContext()
  const { setSelectedTask } = useTaskContext()

  // Get group name from URL
  const groupName = params.groupName as string

  // Group state
  const [group, setGroup] = useState<Group | null>(null)
  const [loadingGroup, setLoadingGroup] = useState(true)
  const [groupError, setGroupError] = useState<string | null>(null)

  // Knowledge bases for this group
  const {
    knowledgeBases,
    loading: kbLoading,
    refresh: refreshKb,
    create,
    update,
    remove,
  } = useKnowledgeBases({
    scope: 'group',
    groupName,
  })

  // Dialog states
  const [showCreateDialog, setShowCreateDialog] = useState(false)
  const [createKbType, setCreateKbType] = useState<KnowledgeBaseType>('notebook')
  const [editingKb, setEditingKb] = useState<KnowledgeBase | null>(null)
  const [deletingKb, setDeletingKb] = useState<KnowledgeBase | null>(null)

  // Search state
  const [searchQuery, setSearchQuery] = useState('')

  // Sidebar state
  const [isMobileSidebarOpen, setIsMobileSidebarOpen] = useState(false)
  const [isCollapsed, setIsCollapsed] = useState(false)

  // Load group info
  useEffect(() => {
    const loadGroup = async () => {
      try {
        setLoadingGroup(true)
        const response = await listGroups()
        const foundGroup = response.items.find(g => g.name === groupName)
        if (foundGroup) {
          setGroup(foundGroup)
        } else {
          setGroupError(t('knowledge:document.groupNotFound'))
        }
      } catch (error) {
        console.error('Failed to load group:', error)
        setGroupError(t('knowledge:document.groupLoadError'))
      } finally {
        setLoadingGroup(false)
      }
    }
    loadGroup()
  }, [groupName, t])

  // Load collapsed state from localStorage
  useEffect(() => {
    const savedCollapsed = localStorage.getItem('task-sidebar-collapsed')
    if (savedCollapsed === 'true') {
      setIsCollapsed(true)
    }
  }, [])

  // Save last active tab
  useEffect(() => {
    saveLastTab('wiki')
  }, [])

  // Filter knowledge bases by search
  const filteredKnowledgeBases = useMemo(() => {
    if (!searchQuery.trim()) return knowledgeBases
    const query = searchQuery.toLowerCase()
    return knowledgeBases.filter(
      kb => kb.name.toLowerCase().includes(query) || kb.description?.toLowerCase().includes(query)
    )
  }, [knowledgeBases, searchQuery])

  // Permission checks based on group role
  const groupRole = group?.my_role
  const canCreate = groupRole === 'Owner' || groupRole === 'Maintainer' || groupRole === 'Developer'
  const canEdit = groupRole === 'Owner' || groupRole === 'Maintainer' || groupRole === 'Developer'
  const canDelete = groupRole === 'Owner' || groupRole === 'Maintainer'

  // Handlers
  const handleToggleCollapsed = () => {
    setIsCollapsed(prev => {
      const newValue = !prev
      localStorage.setItem('task-sidebar-collapsed', String(newValue))
      return newValue
    })
  }

  const handleNewTask = () => {
    setSelectedTask(null)
    clearAllStreams()
    router.replace(paths.chat.getHref())
  }

  const handleBack = () => {
    router.push('/knowledge')
  }

  const handleSelectKb = (kb: KnowledgeBase) => {
    router.push(`/knowledge/document/${kb.id}`)
  }

  const handleCreateKb = (kbType: KnowledgeBaseType) => {
    setCreateKbType(kbType)
    setShowCreateDialog(true)
  }

  const handleCreate = async (data: {
    name: string
    description?: string
    retrieval_config?: Parameters<typeof create>[0]['retrieval_config']
  }) => {
    await create({
      name: data.name,
      description: data.description,
      namespace: groupName,
      retrieval_config: data.retrieval_config,
      kb_type: createKbType,
    })
    setShowCreateDialog(false)
    setCreateKbType('notebook')
    refreshKb()
  }

  const handleUpdate = async (data: Parameters<typeof update>[1]) => {
    if (!editingKb) return
    await update(editingKb.id, data)
    setEditingKb(null)
  }

  const handleDelete = async () => {
    if (!deletingKb) return
    await remove(deletingKb.id)
    setDeletingKb(null)
  }

  const groupDisplayName = group?.display_name || group?.name || groupName

  // Loading state
  if (loadingGroup) {
    return (
      <div className="flex smart-h-screen bg-base text-text-primary items-center justify-center">
        <Spinner />
      </div>
    )
  }

  // Error state
  if (groupError || !group) {
    return (
      <div className="flex smart-h-screen bg-base text-text-primary items-center justify-center">
        <div className="text-center">
          <Users className="w-12 h-12 mx-auto mb-4 text-text-muted opacity-50" />
          <p className="text-text-muted mb-4">
            {groupError || t('knowledge:document.groupNotFound')}
          </p>
          <button
            onClick={handleBack}
            className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-primary hover:bg-primary/10 rounded-md transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            {t('knowledge:document.backToKnowledge')}
          </button>
        </div>
      </div>
    )
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

        {/* Content area */}
        <div className="flex-1 overflow-auto p-6">
          <div className="space-y-4">
            {/* Header with back button and group name */}
            <div className="flex items-center gap-3 mb-4">
              <button
                onClick={handleBack}
                className="p-1.5 rounded-md text-text-muted hover:text-text-primary hover:bg-surface transition-colors"
              >
                <ArrowLeft className="w-5 h-5" />
              </button>
              <Users className="w-5 h-5 text-primary flex-shrink-0" />
              <h2 className="font-medium text-base text-text-primary">{groupDisplayName}</h2>
            </div>

            {/* Content */}
            {kbLoading ? (
              <div className="flex justify-center py-12">
                <Spinner />
              </div>
            ) : knowledgeBases.length === 0 ? (
              canCreate ? (
                <div className="flex flex-col items-center justify-center py-16">
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <Card
                        padding="lg"
                        className="hover:bg-hover transition-colors cursor-pointer flex flex-col items-center justify-center w-64 h-48"
                      >
                        <div className="w-14 h-14 rounded-full bg-primary/10 flex items-center justify-center mb-4">
                          <Plus className="w-8 h-8 text-primary" />
                        </div>
                        <h3 className="font-medium text-base mb-2 text-text-primary">
                          {t('knowledge:document.knowledgeBase.create')}
                        </h3>
                        <p className="text-sm text-text-muted text-center">
                          {t('knowledge:document.knowledgeBase.createDesc')}
                        </p>
                      </Card>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="center" className="w-56">
                      <DropdownMenuItem
                        onClick={() => handleCreateKb('notebook')}
                        className="flex items-start gap-3 py-3"
                      >
                        <BookOpen className="w-5 h-5 text-primary mt-0.5 flex-shrink-0" />
                        <div>
                          <div className="font-medium">
                            {t('knowledge:document.knowledgeBase.typeNotebook')}
                          </div>
                          <div className="text-xs text-text-muted">
                            {t('knowledge:document.knowledgeBase.notebookDesc')}
                          </div>
                        </div>
                      </DropdownMenuItem>
                      <DropdownMenuItem
                        onClick={() => handleCreateKb('classic')}
                        className="flex items-start gap-3 py-3"
                      >
                        <FolderOpen className="w-5 h-5 text-text-secondary mt-0.5 flex-shrink-0" />
                        <div>
                          <div className="font-medium">
                            {t('knowledge:document.knowledgeBase.typeClassic')}
                          </div>
                          <div className="text-xs text-text-muted">
                            {t('knowledge:document.knowledgeBase.classicDesc')}
                          </div>
                        </div>
                      </DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                </div>
              ) : (
                <div className="flex flex-col items-center justify-center py-12 text-text-secondary">
                  <FileText className="w-12 h-12 mb-4 opacity-50" />
                  <p>{t('knowledge:document.knowledgeBase.empty')}</p>
                </div>
              )
            ) : (
              <div className="flex flex-col items-center">
                {/* Search bar */}
                <div className="mb-4 w-full max-w-4xl">
                  <div className="relative w-full max-w-md mx-auto">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted" />
                    <input
                      type="text"
                      className="w-full h-9 pl-9 pr-3 text-sm bg-surface border border-border rounded-md focus:outline-none focus:ring-1 focus:ring-primary"
                      placeholder={t('knowledge:document.knowledgeBase.search')}
                      value={searchQuery}
                      onChange={e => setSearchQuery(e.target.value)}
                    />
                  </div>
                </div>

                <div className="w-full max-w-4xl grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                  {/* Add knowledge base card with dropdown - only show if user can create */}
                  {!searchQuery && canCreate && (
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Card
                          padding="sm"
                          className="hover:bg-hover transition-colors cursor-pointer flex flex-col items-center justify-center h-[140px]"
                        >
                          <div className="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center mb-3">
                            <Plus className="w-6 h-6 text-primary" />
                          </div>
                          <h3 className="font-medium text-sm">
                            {t('knowledge:document.knowledgeBase.create')}
                          </h3>
                        </Card>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="center" className="w-56">
                        <DropdownMenuItem
                          onClick={() => handleCreateKb('notebook')}
                          className="flex items-start gap-3 py-3"
                        >
                          <BookOpen className="w-5 h-5 text-primary mt-0.5 flex-shrink-0" />
                          <div>
                            <div className="font-medium">
                              {t('knowledge:document.knowledgeBase.typeNotebook')}
                            </div>
                            <div className="text-xs text-text-muted">
                              {t('knowledge:document.knowledgeBase.notebookDesc')}
                            </div>
                          </div>
                        </DropdownMenuItem>
                        <DropdownMenuItem
                          onClick={() => handleCreateKb('classic')}
                          className="flex items-start gap-3 py-3"
                        >
                          <FolderOpen className="w-5 h-5 text-text-secondary mt-0.5 flex-shrink-0" />
                          <div>
                            <div className="font-medium">
                              {t('knowledge:document.knowledgeBase.typeClassic')}
                            </div>
                            <div className="text-xs text-text-muted">
                              {t('knowledge:document.knowledgeBase.classicDesc')}
                            </div>
                          </div>
                        </DropdownMenuItem>
                      </DropdownMenuContent>
                    </DropdownMenu>
                  )}

                  {/* Knowledge base cards */}
                  {filteredKnowledgeBases.map(kb => (
                    <KnowledgeBaseCard
                      key={kb.id}
                      knowledgeBase={kb}
                      onClick={() => handleSelectKb(kb)}
                      onEdit={canEdit ? () => setEditingKb(kb) : undefined}
                      onDelete={canDelete ? () => setDeletingKb(kb) : undefined}
                      canEdit={canEdit}
                      canDelete={canDelete}
                    />
                  ))}
                </div>

                {/* No results message */}
                {searchQuery && filteredKnowledgeBases.length === 0 && (
                  <div className="flex flex-col items-center justify-center py-12 text-text-secondary">
                    <FileText className="w-12 h-12 mb-4 opacity-50" />
                    <p>{t('knowledge:document.knowledgeBase.noResults')}</p>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Dialogs */}
      <CreateKnowledgeBaseDialog
        open={showCreateDialog}
        onOpenChange={open => {
          setShowCreateDialog(open)
          if (!open) {
            setCreateKbType('notebook')
          }
        }}
        onSubmit={handleCreate}
        loading={kbLoading}
        scope="group"
        groupName={groupName}
        kbType={createKbType}
      />

      <EditKnowledgeBaseDialog
        open={!!editingKb}
        onOpenChange={open => !open && setEditingKb(null)}
        knowledgeBase={editingKb}
        onSubmit={handleUpdate}
        loading={kbLoading}
      />

      <DeleteKnowledgeBaseDialog
        open={!!deletingKb}
        onOpenChange={open => !open && setDeletingKb(null)}
        knowledgeBase={deletingKb}
        onConfirm={handleDelete}
        loading={kbLoading}
      />
    </div>
  )
}
