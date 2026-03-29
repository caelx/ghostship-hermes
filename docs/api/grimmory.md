# Grimmory API Spec Sheet

## Service Identity

- Product: Grimmory
- Official upstream: `grimmory-tools/grimmory`
- Product positioning in upstream README: successor to BookLore
- Primary API prefix in the backend source: `/api/v1`
- Source of truth for this sheet: official Grimmory backend controller annotations in the upstream repository

## Authentication

The official Grimmory backend source defines authentication under `/api/v1/auth`:

- `POST /api/v1/auth/login`
- `POST /api/v1/auth/refresh`
- `POST /api/v1/auth/register`
- `POST /api/v1/auth/logout`
- `GET /api/v1/auth/remote`

The backend also includes companion auth-related integrations for OIDC, OPDS, Kobo, and KOReader flows.

## Canonical Source Quality

- Official Grimmory repository source code
- No mirrored machine-readable OpenAPI artifact was found in the official repository at documentation time

## Full Endpoint and Use-Case Inventory

This inventory is derived from the official controller mappings in the Grimmory repository. It documents the broader upstream API surface, not just the subset currently used by `ghostship-grimmory`.

### Authentication
- `POST /api/v1/auth/login`
- `POST /api/v1/auth/refresh`
- `POST /api/v1/auth/register`
- `GET /api/v1/auth/remote`
- Source: `booklore-api/src/main/java/org/booklore/controller/AuthenticationController.java`

### Logout
- `POST /api/v1/auth/logout`
- Source: `booklore-api/src/main/java/org/booklore/controller/LogoutController.java`

### Version
- `GET /api/v1/version`
- `GET /api/v1/version/changelog`
- Source: `booklore-api/src/main/java/org/booklore/controller/VersionController.java`

### Healthcheck
- `GET /api/v1/healthcheck`
- Source: `booklore-api/src/main/java/org/booklore/controller/HealthcheckController.java`

### Setup
- `POST /api/v1/setup`
- `GET /api/v1/setup/status`
- Source: `booklore-api/src/main/java/org/booklore/controller/SetupController.java`

### Library
- `GET /api/v1/libraries`
- `POST /api/v1/libraries`
- `GET /api/v1/libraries/health`
- `POST /api/v1/libraries/scan`
- `DELETE /api/v1/libraries/{libraryId}`
- `GET /api/v1/libraries/{libraryId}`
- `PUT /api/v1/libraries/{libraryId}`
- `GET /api/v1/libraries/{libraryId}/book`
- `GET /api/v1/libraries/{libraryId}/book/{bookId}`
- `PATCH /api/v1/libraries/{libraryId}/file-naming-pattern`
- `GET /api/v1/libraries/{libraryId}/format-counts`
- `PUT /api/v1/libraries/{libraryId}/refresh`
- Source: `booklore-api/src/main/java/org/booklore/controller/LibraryController.java`

### Book
- `DELETE /api/v1/books`
- `GET /api/v1/books`
- `GET /api/v1/books/batch`
- `POST /api/v1/books/duplicates`
- `PUT /api/v1/books/personal-rating`
- `POST /api/v1/books/physical`
- `POST /api/v1/books/progress`
- `POST /api/v1/books/reset-personal-rating`
- `POST /api/v1/books/reset-progress`
- `POST /api/v1/books/shelves`
- `POST /api/v1/books/status`
- `GET /api/v1/books/{bookId}`
- `GET /api/v1/books/{bookId}/cbx/metadata/comicinfo`
- `GET /api/v1/books/{bookId}/content`
- `GET /api/v1/books/{bookId}/download`
- `GET /api/v1/books/{bookId}/download-all`
- `GET /api/v1/books/{bookId}/file-metadata`
- `PATCH /api/v1/books/{bookId}/physical`
- `GET /api/v1/books/{bookId}/viewer-setting`
- `PUT /api/v1/books/{bookId}/viewer-setting`
- `GET /api/v1/books/{id}/recommendations`
- `POST /api/v1/books/{targetBookId}/attach-file`
- Source: `booklore-api/src/main/java/org/booklore/controller/BookController.java`

### Author
- `DELETE /api/v1/authors`
- `GET /api/v1/authors`
- `POST /api/v1/authors/auto-match`
- `GET /api/v1/authors/book/{bookId}`
- `GET /api/v1/authors/by-name`
- `POST /api/v1/authors/unmatch`
- `GET /api/v1/authors/{authorId}`
- `PUT /api/v1/authors/{authorId}`
- `POST /api/v1/authors/{authorId}/match`
- `POST /api/v1/authors/{authorId}/photo/upload`
- `POST /api/v1/authors/{authorId}/photo/url`
- `POST /api/v1/authors/{authorId}/quick-match`
- `GET /api/v1/authors/{authorId}/search-metadata`
- `GET /api/v1/authors/{authorId}/search-photos`
- Source: `booklore-api/src/main/java/org/booklore/controller/AuthorController.java`

### Shelf
- `GET /api/v1/shelves`
- `POST /api/v1/shelves`
- `DELETE /api/v1/shelves/{shelfId}`
- `GET /api/v1/shelves/{shelfId}`
- `PUT /api/v1/shelves/{shelfId}`
- `GET /api/v1/shelves/{shelfId}/books`
- Source: `booklore-api/src/main/java/org/booklore/controller/ShelfController.java`

### Magic Shelf
- `GET /api/magic-shelves`
- `POST /api/magic-shelves`
- `DELETE /api/magic-shelves/{id}`
- `GET /api/magic-shelves/{id}`
- Source: `booklore-api/src/main/java/org/booklore/controller/MagicShelfController.java`

### Task
- `GET /api/v1/tasks`
- `GET /api/v1/tasks/last`
- `POST /api/v1/tasks/start`
- `DELETE /api/v1/tasks/{taskId}/cancel`
- `PATCH /api/v1/tasks/{taskType}/cron`
- Source: `booklore-api/src/main/java/org/booklore/controller/TaskController.java`

### Metadata
- `PUT /api/v1/books/bulk-edit-metadata`
- `GET /api/v1/books/metadata/detail/{provider}/{providerItemId}`
- `POST /api/v1/books/metadata/isbn-lookup`
- `POST /api/v1/books/metadata/manage/consolidate`
- `POST /api/v1/books/metadata/manage/delete`
- `POST /api/v1/books/metadata/recalculate-match-scores`
- `PUT /api/v1/books/metadata/toggle-all-lock`
- `PUT /api/v1/books/metadata/toggle-field-locks`
- `PUT /api/v1/books/{bookId}/metadata`
- `POST /api/v1/books/{bookId}/metadata/prospective`
- Source: `booklore-api/src/main/java/org/booklore/controller/MetadataController.java`

### Metadata Task
- `GET /api/metadata/tasks/active`
- `DELETE /api/metadata/tasks/{taskId}`
- `GET /api/metadata/tasks/{taskId}`
- `POST /api/metadata/tasks/{taskId}/proposals/{proposalId}/status`
- Source: `booklore-api/src/main/java/org/booklore/controller/MetadataTaskController.java`

### Bookdrop File
- `GET /api/v1/bookdrop/files`
- `POST /api/v1/bookdrop/files/bulk-edit`
- `POST /api/v1/bookdrop/files/discard`
- `POST /api/v1/bookdrop/files/extract-pattern`
- `POST /api/v1/bookdrop/imports/finalize`
- `GET /api/v1/bookdrop/notification`
- `POST /api/v1/bookdrop/rescan`
- Source: `booklore-api/src/main/java/org/booklore/controller/BookdropFileController.java`

### File Upload
- `POST /api/v1/files/upload`
- `POST /api/v1/files/upload/bookdrop`
- Source: `booklore-api/src/main/java/org/booklore/controller/FileUploadController.java`

### File Move
- `POST /api/v1/files/move`
- Source: `booklore-api/src/main/java/org/booklore/controller/FileMoveController.java`

### Additional File
- `GET /api/v1/books/{bookId}/files`
- `POST /api/v1/books/{bookId}/files`
- `DELETE /api/v1/books/{bookId}/files/{fileId}`
- `POST /api/v1/books/{bookId}/files/{fileId}/detach`
- `GET /api/v1/books/{bookId}/files/{fileId}/download`
- Source: `booklore-api/src/main/java/org/booklore/controller/AdditionalFileController.java`

### Book Media
- `GET /api/v1/media/author/{authorId}/photo`
- `GET /api/v1/media/author/{authorId}/thumbnail`
- `GET /api/v1/media/book/{bookId}/audiobook-cover`
- `GET /api/v1/media/book/{bookId}/audiobook-thumbnail`
- `GET /api/v1/media/book/{bookId}/cbx/pages/{pageNumber}`
- `GET /api/v1/media/book/{bookId}/cover`
- `GET /api/v1/media/book/{bookId}/thumbnail`
- `GET /api/v1/media/bookdrop/{bookdropId}/cover`
- Source: `booklore-api/src/main/java/org/booklore/controller/BookMediaController.java`

### Book Cover
- `POST /api/v1/books/bulk-generate-custom-covers`
- `POST /api/v1/books/bulk-regenerate-covers`
- `POST /api/v1/books/bulk-upload-cover`
- `POST /api/v1/books/regenerate-covers`
- `POST /api/v1/books/{bookId}/generate-custom-audiobook-cover`
- `POST /api/v1/books/{bookId}/generate-custom-cover`
- `POST /api/v1/books/{bookId}/metadata/audiobook-cover/from-url`
- `POST /api/v1/books/{bookId}/metadata/audiobook-cover/upload`
- `POST /api/v1/books/{bookId}/metadata/cover/from-url`
- `POST /api/v1/books/{bookId}/metadata/cover/upload`
- `POST /api/v1/books/{bookId}/metadata/covers`
- `POST /api/v1/books/{bookId}/regenerate-audiobook-cover`
- `POST /api/v1/books/{bookId}/regenerate-cover`
- Source: `booklore-api/src/main/java/org/booklore/controller/BookCoverController.java`

### Book Mark
- `POST /api/v1/bookmarks`
- `GET /api/v1/bookmarks/book/{bookId}`
- `DELETE /api/v1/bookmarks/{bookmarkId}`
- `GET /api/v1/bookmarks/{bookmarkId}`
- `PUT /api/v1/bookmarks/{bookmarkId}`
- Source: `booklore-api/src/main/java/org/booklore/controller/BookMarkController.java`

### Book Note
- `POST /api/v1/book-notes`
- `GET /api/v1/book-notes/book/{bookId}`
- `DELETE /api/v1/book-notes/{noteId}`
- Source: `booklore-api/src/main/java/org/booklore/controller/BookNoteController.java`

### Book Notes V2
- `POST /api/v2/book-notes`
- `GET /api/v2/book-notes/book/{bookId}`
- `DELETE /api/v2/book-notes/{noteId}`
- `GET /api/v2/book-notes/{noteId}`
- `PUT /api/v2/book-notes/{noteId}`
- Source: `booklore-api/src/main/java/org/booklore/controller/BookNotesV2Controller.java`

### Book Review
- `DELETE /api/v1/reviews/book/{bookId}`
- `GET /api/v1/reviews/book/{bookId}`
- `POST /api/v1/reviews/book/{bookId}/refresh`
- `DELETE /api/v1/reviews/{id}`
- Source: `booklore-api/src/main/java/org/booklore/controller/BookReviewController.java`

### Annotation
- `POST /api/v1/annotations`
- `GET /api/v1/annotations/book/{bookId}`
- `DELETE /api/v1/annotations/{annotationId}`
- `GET /api/v1/annotations/{annotationId}`
- `PUT /api/v1/annotations/{annotationId}`
- Source: `booklore-api/src/main/java/org/booklore/controller/AnnotationController.java`

### Pdf Annotation
- `DELETE /api/v1/pdf-annotations/book/{bookId}`
- `GET /api/v1/pdf-annotations/book/{bookId}`
- `PUT /api/v1/pdf-annotations/book/{bookId}`
- Source: `booklore-api/src/main/java/org/booklore/controller/PdfAnnotationController.java`

### Notebook
- `GET /api/v1/notebook`
- `GET /api/v1/notebook/books`
- `GET /api/v1/notebook/export`
- Source: `booklore-api/src/main/java/org/booklore/controller/NotebookController.java`

### Reading Session
- `POST /api/v1/reading-sessions`
- `GET /api/v1/reading-sessions/book/{bookId}`
- Source: `booklore-api/src/main/java/org/booklore/controller/ReadingSessionController.java`

### App Author
- `GET /api/v1/app/authors`
- `GET /api/v1/app/authors/{authorId}`
- Source: `booklore-api/src/main/java/org/booklore/app/controller/AppAuthorController.java`

### App Book
- `GET /api/v1/app/books`
- `GET /api/v1/app/books/continue-listening`
- `GET /api/v1/app/books/continue-reading`
- `GET /api/v1/app/books/random`
- `GET /api/v1/app/books/recently-added`
- `GET /api/v1/app/books/recently-scanned`
- `GET /api/v1/app/books/search`
- `GET /api/v1/app/books/{bookId}`
- `PUT /api/v1/app/books/{bookId}/rating`
- `PUT /api/v1/app/books/{bookId}/status`
- Source: `booklore-api/src/main/java/org/booklore/app/controller/AppBookController.java`

### App Filter
- `GET /api/v1/app/filter-options`
- Source: `booklore-api/src/main/java/org/booklore/app/controller/AppFilterController.java`

### App Library
- `GET /api/v1/app/libraries`
- Source: `booklore-api/src/main/java/org/booklore/app/controller/AppLibraryController.java`

### App Notebook
- `GET /api/v1/app/notebook/books`
- `GET /api/v1/app/notebook/books/{bookId}/entries`
- `DELETE /api/v1/app/notebook/entries/{entryId}`
- `PUT /api/v1/app/notebook/entries/{entryId}`
- Source: `booklore-api/src/main/java/org/booklore/app/controller/AppNotebookController.java`

### App Series
- `GET /api/v1/app/series`
- `GET /api/v1/app/series/{seriesName}/books`
- Source: `booklore-api/src/main/java/org/booklore/app/controller/AppSeriesController.java`

### App Shelf
- `GET /api/v1/app/shelves`
- `GET /api/v1/app/shelves/magic`
- `GET /api/v1/app/shelves/magic/{magicShelfId}/books`
- Source: `booklore-api/src/main/java/org/booklore/app/controller/AppShelfController.java`

### App User
- `GET /api/v1/app/users/me`
- Source: `booklore-api/src/main/java/org/booklore/app/controller/AppUserController.java`

### User
- `GET /api/v1/users`
- `PUT /api/v1/users/change-password`
- `PUT /api/v1/users/change-user-password`
- `GET /api/v1/users/me`
- `DELETE /api/v1/users/{id}`
- `GET /api/v1/users/{id}`
- `PUT /api/v1/users/{id}`
- `PUT /api/v1/users/{id}/settings`
- Source: `booklore-api/src/main/java/org/booklore/controller/UserController.java`

### User Stats
- `GET /api/v1/user-stats/listening/authors`
- `GET /api/v1/user-stats/listening/completion`
- `GET /api/v1/user-stats/listening/finish-funnel`
- `GET /api/v1/user-stats/listening/genres`
- `GET /api/v1/user-stats/listening/heatmap/monthly`
- `GET /api/v1/user-stats/listening/longest-books`
- `GET /api/v1/user-stats/listening/monthly-pace`
- `GET /api/v1/user-stats/listening/peak-hours`
- `GET /api/v1/user-stats/listening/session-scatter`
- `GET /api/v1/user-stats/listening/weekly-trend`
- `GET /api/v1/user-stats/reading/book-completion-heatmap`
- `GET /api/v1/user-stats/reading/book-distributions`
- `GET /api/v1/user-stats/reading/book-timeline`
- `GET /api/v1/user-stats/reading/completion-race`
- `GET /api/v1/user-stats/reading/completion-timeline`
- `GET /api/v1/user-stats/reading/dates`
- `GET /api/v1/user-stats/reading/favorite-days`
- `GET /api/v1/user-stats/reading/genres`
- `GET /api/v1/user-stats/reading/heatmap`
- `GET /api/v1/user-stats/reading/heatmap/monthly`
- `GET /api/v1/user-stats/reading/page-turner-scores`
- `GET /api/v1/user-stats/reading/peak-hours`
- `GET /api/v1/user-stats/reading/session-scatter`
- `GET /api/v1/user-stats/reading/speed`
- `GET /api/v1/user-stats/reading/streak`
- `GET /api/v1/user-stats/reading/timeline`
- Source: `booklore-api/src/main/java/org/booklore/controller/UserStatsController.java`

### App Setting
- `GET /api/v1/settings`
- `PUT /api/v1/settings`
- `POST /api/v1/settings/oidc/test`
- Source: `booklore-api/src/main/java/org/booklore/controller/AppSettingController.java`

### Public App Setting
- `GET /api/v1/public-settings`
- Source: `booklore-api/src/main/java/org/booklore/controller/PublicAppSettingController.java`

### Content Restriction
- `DELETE /api/v1/users/{userId}/content-restrictions`
- `GET /api/v1/users/{userId}/content-restrictions`
- `POST /api/v1/users/{userId}/content-restrictions`
- `PUT /api/v1/users/{userId}/content-restrictions`
- `DELETE /api/v1/users/{userId}/content-restrictions/{restrictionId}`
- Source: `booklore-api/src/main/java/org/booklore/controller/ContentRestrictionController.java`

### Oidc Auth
- `POST /api/v1/auth/oidc/backchannel-logout`
- `POST /api/v1/auth/oidc/callback`
- `POST /api/v1/auth/oidc/mobile/callback`
- `GET /api/v1/auth/oidc/redirect`
- `GET /api/v1/auth/oidc/state`
- Source: `booklore-api/src/main/java/org/booklore/controller/OidcAuthController.java`

### Oidc Group Mapping
- `GET /api/v1/admin/oidc-group-mappings`
- `POST /api/v1/admin/oidc-group-mappings`
- `DELETE /api/v1/admin/oidc-group-mappings/{id}`
- `PUT /api/v1/admin/oidc-group-mappings/{id}`
- Source: `booklore-api/src/main/java/org/booklore/controller/OidcGroupMappingController.java`

### Hardcover Sync Settings
- `GET /api/v1/hardcover-sync-settings`
- `PUT /api/v1/hardcover-sync-settings`
- Source: `booklore-api/src/main/java/org/booklore/controller/HardcoverSyncSettingsController.java`

### Email Provider V2
- `GET /api/v1/email/providers`
- `POST /api/v1/email/providers`
- `DELETE /api/v1/email/providers/{id}`
- `GET /api/v1/email/providers/{id}`
- `PUT /api/v1/email/providers/{id}`
- `PATCH /api/v1/email/providers/{id}/set-default`
- Source: `booklore-api/src/main/java/org/booklore/controller/EmailProviderV2Controller.java`

### Email Recipient V2
- `GET /api/v1/email/recipients`
- `POST /api/v1/email/recipients`
- `DELETE /api/v1/email/recipients/{id}`
- `GET /api/v1/email/recipients/{id}`
- `PUT /api/v1/email/recipients/{id}`
- `PATCH /api/v1/email/recipients/{id}/set-default`
- Source: `booklore-api/src/main/java/org/booklore/controller/EmailRecipientV2Controller.java`

### Send Email V2
- `POST /api/v1/email/book`
- `POST /api/v1/email/book/{bookId}`
- Source: `booklore-api/src/main/java/org/booklore/controller/SendEmailV2Controller.java`

### Audit Log
- `GET /api/v1/audit-logs`
- `GET /api/v1/audit-logs/usernames`
- Source: `booklore-api/src/main/java/org/booklore/controller/AuditLogController.java`

### Path
- `GET /api/v1/path`
- Source: `booklore-api/src/main/java/org/booklore/controller/PathController.java`

### Sidecar
- `GET /api/v1/books/{bookId}/sidecar`
- `POST /api/v1/books/{bookId}/sidecar/export`
- `POST /api/v1/books/{bookId}/sidecar/import`
- `GET /api/v1/books/{bookId}/sidecar/status`
- `POST /api/v1/libraries/{libraryId}/sidecar/export-all`
- `POST /api/v1/libraries/{libraryId}/sidecar/import-all`
- Source: `booklore-api/src/main/java/org/booklore/controller/SidecarController.java`

### Custom Font
- `GET /api/v1/custom-fonts`
- `POST /api/v1/custom-fonts/upload`
- `DELETE /api/v1/custom-fonts/{fontId}`
- `GET /api/v1/custom-fonts/{fontId}/file`
- Source: `booklore-api/src/main/java/org/booklore/controller/CustomFontController.java`

### Icon
- `GET /api/v1/icons`
- `POST /api/v1/icons`
- `GET /api/v1/icons/all/content`
- `POST /api/v1/icons/batch`
- `DELETE /api/v1/icons/{svgName}`
- `GET /api/v1/icons/{svgName}/content`
- Source: `booklore-api/src/main/java/org/booklore/controller/IconController.java`

### Kobo
- `POST /api/kobo/{token}/v1/analytics/gettests`
- `POST /api/kobo/{token}/v1/auth/device`
- `GET /api/kobo/{token}/v1/books/{bookId}/download`
- `GET /api/kobo/{token}/v1/books/{imageId}/thumbnail/{width}/{height}/false/image.jpg`
- `GET /api/kobo/{token}/v1/books/{imageId}/thumbnail/{width}/{height}/{quality}/{isGreyscale}/image.jpg`
- `GET /api/kobo/{token}/v1/books/{imageId}/{version}/thumbnail/{width}/{height}/false/image.jpg`
- `GET /api/kobo/{token}/v1/books/{imageId}/{version}/thumbnail/{width}/{height}/{quality}/{isGreyscale}/image.jpg`
- `GET /api/kobo/{token}/v1/initialization`
- `GET /api/kobo/{token}/v1/library/sync`
- `DELETE /api/kobo/{token}/v1/library/{bookId}`
- `GET /api/kobo/{token}/v1/library/{bookId}/metadata`
- `GET /api/kobo/{token}/v1/library/{bookId}/state`
- `PUT /api/kobo/{token}/v1/library/{bookId}/state`
- Source: `booklore-api/src/main/java/org/booklore/controller/KoboController.java`

### Kobo Settings
- `GET /api/v1/kobo-settings`
- `PUT /api/v1/kobo-settings`
- `PUT /api/v1/kobo-settings/token`
- Source: `booklore-api/src/main/java/org/booklore/controller/KoboSettingsController.java`

### Koreader
- `PUT /api/koreader/syncs/progress`
- `GET /api/koreader/syncs/progress/{bookHash}`
- `GET /api/koreader/users/auth`
- `POST /api/koreader/users/create`
- Source: `booklore-api/src/main/java/org/booklore/controller/KoreaderController.java`

### Koreader User
- `GET /api/v1/koreader-users/me`
- `PUT /api/v1/koreader-users/me`
- `PATCH /api/v1/koreader-users/me/sync`
- `PATCH /api/v1/koreader-users/me/sync-progress-with-booklore`
- Source: `booklore-api/src/main/java/org/booklore/controller/KoreaderUserController.java`

### Komga
- `GET /komga/api/v1/books`
- `GET /komga/api/v1/books/{bookId}`
- `GET /komga/api/v1/books/{bookId}/file`
- `GET /komga/api/v1/books/{bookId}/pages`
- `GET /komga/api/v1/books/{bookId}/pages/{pageNumber}`
- `GET /komga/api/v1/books/{bookId}/thumbnail`
- `GET /komga/api/v1/collections`
- `GET /komga/api/v1/libraries`
- `GET /komga/api/v1/libraries/{libraryId}`
- `GET /komga/api/v1/series`
- `GET /komga/api/v1/series/{seriesId}`
- `GET /komga/api/v1/series/{seriesId}/books`
- `GET /komga/api/v1/series/{seriesId}/thumbnail`
- `GET /komga/api/v2/users/me`
- Source: `booklore-api/src/main/java/org/booklore/controller/KomgaController.java`

### Opds
- `GET /api/v1/opds`
- `GET /api/v1/opds/authors`
- `GET /api/v1/opds/catalog`
- `GET /api/v1/opds/libraries`
- `GET /api/v1/opds/magic-shelves`
- `GET /api/v1/opds/recent`
- `GET /api/v1/opds/search.opds`
- `GET /api/v1/opds/series`
- `GET /api/v1/opds/shelves`
- `GET /api/v1/opds/surprise`
- `GET /api/v1/opds/{bookId}/cover`
- `GET /api/v1/opds/{bookId}/download`
- Source: `booklore-api/src/main/java/org/booklore/controller/OpdsController.java`

### Opds User V2
- `GET /api/v2/opds-users`
- `POST /api/v2/opds-users`
- `DELETE /api/v2/opds-users/{id}`
- `PATCH /api/v2/opds-users/{id}`
- Source: `booklore-api/src/main/java/org/booklore/controller/OpdsUserV2Controller.java`

### Audiobook Reader
- `GET /api/v1/audiobooks/{bookId}/cover`
- `GET /api/v1/audiobooks/{bookId}/info`
- `GET /api/v1/audiobooks/{bookId}/stream`
- `GET /api/v1/audiobooks/{bookId}/track/{trackIndex}/stream`
- Source: `booklore-api/src/main/java/org/booklore/controller/AudiobookReaderController.java`

### Epub Reader
- `GET /api/v1/epub/{bookId}/file/**`
- `GET /api/v1/epub/{bookId}/info`
- Source: `booklore-api/src/main/java/org/booklore/controller/EpubReaderController.java`

### Pdf Reader
- `GET /api/v1/pdf/{bookId}/info`
- `GET /api/v1/pdf/{bookId}/pages`
- Source: `booklore-api/src/main/java/org/booklore/controller/PdfReaderController.java`

### Cbx Reader
- `GET /api/v1/cbx/{bookId}/page-info`
- `GET /api/v1/cbx/{bookId}/pages`
- Source: `booklore-api/src/main/java/org/booklore/controller/CbxReaderController.java`

## Repo Utility Surface

`ghostship-grimmory` currently targets a narrower BookLore-compatible subset of the Grimmory API:

- auth login
- version lookup
- books
- libraries
- authors
- shelves
- tasks

The upstream Grimmory backend now exposes substantially more surface than the current CLI wraps.

## Source Material

- Official repository: <https://github.com/grimmory-tools/grimmory>
- Official README: <https://raw.githubusercontent.com/grimmory-tools/grimmory/main/README.md>
- Official backend controller tree: <https://api.github.com/repos/grimmory-tools/grimmory/git/trees/main?recursive=1>
