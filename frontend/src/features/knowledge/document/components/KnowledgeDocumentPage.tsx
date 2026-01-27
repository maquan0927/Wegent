// SPDX-FileCopyrightText: 2025 Weibo, Inc.
//
// SPDX-License-Identifier: Apache-2.0

'use client'

import { useState, useEffect, useMemo } from 'react'
import { useRouter } from 'next/navigation'
import { Users, User, Plus, FileText, Globe, Search, BookOpen, FolderOpen } from 'lucide-react'
import { Spinner } from '@/components/ui/spinner'
import { Card } from '@/components/ui/card'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown'
import { KnowledgeBaseCard } from './KnowledgeBaseCard'
import { GroupCard } from './GroupCard'
import { CreateKnowledgeBaseDialog } from './CreateKnowledgeBaseDialog'
import { EditKnowledgeBaseDialog } from './EditKnowledgeBaseDialog'
import { DeleteKnowledgeBaseDialog } from './DeleteKnowledgeBaseDialog'
import { useTranslation } from '@/hooks/useTranslation'
import { listGroups } from '@/apis/groups'
import { useKnowledgeBases } from '../hooks/useKnowledgeBases'
import type { Group } from '@/types/group'
import type { KnowledgeBase, KnowledgeBaseType } from '@/types/knowledge'

type DocumentTabType = 'personal' | 'group' | 'external'

interface DocumentTab {
  id: DocumentTabType
  labelKey: string
  icon: React.ReactNode
  disabled?: boolean
}

const tabs: DocumentTab[] = [
  {
    id: 'personal',
    labelKey: 'knowledge:document.tabs.personal',
    icon: <User className="w-4 h-4" />,
  },
  {
    id: 'group',
    labelKey: 'knowledge:document.tabs.group',
    icon: <Users className="w-4 h-4" />,
  },
  {
    id: 'external',
    labelKey: 'knowledge:document.tabs.external',
    icon: <Globe className="w-4 h-4" />,
    disabled: true,
  },
]

export function KnowledgeDocumentPage() {
  const { t } = useTranslation()
  const router = useRouter()
  const [activeTab, setActiveTab] = useState<DocumentTabType>('personal')
  const [groups, setGroups] = useState<Group[]>([])
  const [loadingGroups, setLoadingGroups] = useState(true)

  // Dialog states
  const [showCreateDialog, setShowCreateDialog] = useState(false)
  const [createKbType, setCreateKbType] = useState<KnowledgeBaseType>('notebook')
  const [editingKb, setEditingKb] = useState<KnowledgeBase | null>(null)
  const [deletingKb, setDeletingKb] = useState<KnowledgeBase | null>(null)

  // Personal knowledge bases
  const personalKb = useKnowledgeBases({ scope: 'personal' })

  // Load user's groups
  useEffect(() => {
    const loadGroups = async () => {
      try {
        const response = await listGroups()
        setGroups(response.items || [])
      } catch (error) {
        console.error('Failed to load groups:', error)
      } finally {
        setLoadingGroups(false)
      }
    }
    loadGroups()
  }, [])

  const handleCreateKb = (kbType: KnowledgeBaseType) => {
    setCreateKbType(kbType)
    setShowCreateDialog(true)
  }

  const handleCreate = async (data: {
    name: string
    description?: string
    retrieval_config?: Parameters<typeof personalKb.create>[0]['retrieval_config']
    summary_enabled?: boolean
    summary_model_ref?: Parameters<typeof personalKb.create>[0]['summary_model_ref'] | null
  }) => {
    await personalKb.create({
      name: data.name,
      description: data.description,
      namespace: 'default',
      retrieval_config: data.retrieval_config,
      summary_enabled: data.summary_enabled,
      summary_model_ref: data.summary_model_ref,
      kb_type: createKbType,
    })
    setShowCreateDialog(false)
    personalKb.refresh()
    setCreateKbType('notebook')
  }

  const handleUpdate = async (data: Parameters<typeof personalKb.update>[1]) => {
    if (!editingKb) return
    await personalKb.update(editingKb.id, data)
    setEditingKb(null)
  }

  const handleDelete = async () => {
    if (!deletingKb) return
    await personalKb.remove(deletingKb.id)
    setDeletingKb(null)
  }

  // Navigate to knowledge base chat page
  const handleSelectKb = (kb: KnowledgeBase) => {
    router.push(`/knowledge/document/${kb.id}`)
  }

  return (
    <div className="space-y-4">
      {/* Tab navigation - left aligned */}
      <div className="flex items-center gap-1">
        {tabs.map(tab => {
          const isActive = activeTab === tab.id
          return (
            <button
              key={tab.id}
              onClick={() => !tab.disabled && setActiveTab(tab.id)}
              disabled={tab.disabled}
              className={`
                relative flex items-center gap-2 px-4 py-2 text-sm font-medium whitespace-nowrap rounded-md transition-colors duration-200
                ${
                  isActive
                    ? 'text-primary bg-primary/10'
                    : tab.disabled
                      ? 'text-text-muted cursor-not-allowed'
                      : 'text-text-secondary hover:text-text-primary hover:bg-muted'
                }
              `}
            >
              {tab.icon}
              <span>{t(tab.labelKey)}</span>
              {tab.disabled && (
                <span className="ml-1 text-xs px-1.5 py-0.5 rounded-full bg-muted text-text-muted">
                  {t('knowledge:coming_soon')}
                </span>
              )}
            </button>
          )
        })}
      </div>

      {/* Tab content */}
      <div>
        {activeTab === 'personal' && (
          <PersonalKnowledgeContent
            knowledgeBases={personalKb.knowledgeBases}
            loading={personalKb.loading}
            onSelectKb={handleSelectKb}
            onEditKb={setEditingKb}
            onDeleteKb={setDeletingKb}
            onCreateKb={kbType => handleCreateKb(kbType)}
          />
        )}

        {activeTab === 'group' && (
          <GroupKnowledgeContent groups={groups} loadingGroups={loadingGroups} />
        )}

        {activeTab === 'external' && (
          <div className="flex flex-col items-center justify-center py-16 text-text-muted">
            <Globe className="w-12 h-12 mb-4 opacity-50" />
            <p>{t('knowledge:coming_soon')}</p>
          </div>
        )}
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
        loading={personalKb.loading}
        scope="personal"
        kbType={createKbType}
      />

      <EditKnowledgeBaseDialog
        open={!!editingKb}
        onOpenChange={open => !open && setEditingKb(null)}
        knowledgeBase={editingKb}
        onSubmit={handleUpdate}
        loading={personalKb.loading}
      />

      <DeleteKnowledgeBaseDialog
        open={!!deletingKb}
        onOpenChange={open => !open && setDeletingKb(null)}
        knowledgeBase={deletingKb}
        onConfirm={handleDelete}
        loading={personalKb.loading}
      />
    </div>
  )
}

// Personal knowledge content component
interface PersonalKnowledgeContentProps {
  knowledgeBases: KnowledgeBase[]
  loading: boolean
  onSelectKb: (kb: KnowledgeBase) => void
  onEditKb: (kb: KnowledgeBase) => void
  onDeleteKb: (kb: KnowledgeBase) => void
  onCreateKb: (kbType: KnowledgeBaseType) => void
}

function PersonalKnowledgeContent({
  knowledgeBases,
  loading,
  onSelectKb,
  onEditKb,
  onDeleteKb,
  onCreateKb,
}: PersonalKnowledgeContentProps) {
  const { t } = useTranslation()
  const [searchQuery, setSearchQuery] = useState('')

  const filteredKnowledgeBases = useMemo(() => {
    if (!searchQuery.trim()) return knowledgeBases
    const query = searchQuery.toLowerCase()
    return knowledgeBases.filter(
      kb => kb.name.toLowerCase().includes(query) || kb.description?.toLowerCase().includes(query)
    )
  }, [knowledgeBases, searchQuery])

  if (loading) {
    return (
      <div className="flex justify-center py-12">
        <Spinner />
      </div>
    )
  }

  if (knowledgeBases.length === 0) {
    return (
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
              onClick={() => onCreateKb('notebook')}
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
              onClick={() => onCreateKb('classic')}
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
    )
  }

  return (
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
        {/* Add knowledge base card with dropdown */}
        {!searchQuery && (
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
                onClick={() => onCreateKb('notebook')}
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
                onClick={() => onCreateKb('classic')}
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
            onClick={() => onSelectKb(kb)}
            onEdit={() => onEditKb(kb)}
            onDelete={() => onDeleteKb(kb)}
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
  )
}

// Group knowledge content component
interface GroupKnowledgeContentProps {
  groups: Group[]
  loadingGroups: boolean
}

function GroupKnowledgeContent({ groups, loadingGroups }: GroupKnowledgeContentProps) {
  const { t } = useTranslation()
  const router = useRouter()

  if (loadingGroups) {
    return (
      <div className="flex justify-center py-12">
        <Spinner />
      </div>
    )
  }

  if (groups.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-12 text-text-secondary">
        <Users className="w-12 h-12 mb-4 opacity-50" />
        <p className="text-sm">{t('knowledge:document.noGroupHint')}</p>
      </div>
    )
  }

  // Navigate to group knowledge base list page
  const handleGroupClick = (group: Group) => {
    router.push(`/knowledge/group/${group.name}`)
  }

  // Show group cards grid - centered
  return (
    <div className="flex flex-col items-center">
      <div className="w-full max-w-4xl grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
        {groups.map(group => (
          <GroupCard key={group.name} group={group} onClick={() => handleGroupClick(group)} />
        ))}
      </div>
    </div>
  )
}
