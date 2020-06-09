# Bluarchive, A Bluprint Downloader
Bluprint, formerly Craftsy, has
[announced](https://www.mybluprint.com/article/letter-to-our-bluprint-customers)
that they are closing, without yet announcing a method of downloading purchased
content. This project is intended to allow customers to preserve their
purchases.

## Features
Saves patterns, class materials, and class videos, including muxed subtitles
and chapters. Also preserves original vtt subtitles, since they can't go into
mp4, and metadata for patterns and classes.

Abridged output example:
```
Patterns/patterns.json
Patterns/Funktional Threads Christmas Stocking/stocking_aiid894970.pdf
Making Leather Bags (272)/playlist.json
Making Leather Bags (272)/1. Meet Don Morin & Plan Your Bag.mp4
Making Leather Bags (272)/1. Meet Don Morin & Plan Your Bag.vtt
Making Leather Bags (272)/materials/making-leather-bags-instructions.pdf
```

## How to Use
* Create a virtualenv: `virtualenv -p python3 venv`
* Activate the virtualenv: `. venv/bin/activate`
* Install bluarchive: `pip install bluarchive`
* Run bluarchive to create a template config: `bluarchive`
* Copy your bluprint cookies into bluarchive.ini
* Make sure everything you want to download is unarchived on the bluprint site!
    (Or remove those checks in the code)
* Run bluarchive again to download the content: `bluarchive`

## Development
`BLU_TEST=1` in env will download one pattern, one class's materials, and one
video. `=2` will download one pattern and one entire class.

## Some Web API Endpoints
Base URL: `https://api.mybluprint.com/`

List all enrolled courses. No authentication required...  
`/enrollments?userId={user_id}`

Playlist contents and metadata, including all episodes and their chapters  
`/m/playlists/{playlist_id}`

CDN URLs for an episode, HLS and mp4  
`/m/videos/secure/episodes/{episode_id}`

List pattern entitlements  
`/users/{user_id}/patterns?pageSize=99999&sortBy=RESOURCE_NAME`

CDN URLs for a pattern  
`/users/{user_id}/patterns/{pattern_id}/patternDownloadLinks`

## App API Endpoints
```
/analytics/videoConsumptionEvents
/assets/uploadLinks
/configs
/enrollments
/login
/users
/users/{userId}/carts
/users/{userId}/carts/{cardId}
/users/{userId}/checkoutConfirmation
/users/{userId}/courseMaterials/{materialsId}/downloadLogs
/users/{userId}/enrollments
/users/{userId}/enrollments/patterns
/users/{userId}/patterns/{patternId}/detailedDownloadLinks
/users/{userId}/profile
/b/affinities
/b/appExploreScreens/apps-explore-screen
/b/homeScreens/apps-home-screen
/b/libraryScreens/apps-library-screen
/b/playlists/{playlistId}/materials
/b/playlists/{playlistId}/summary
/b/searchResults/apps-search-results
/b/typeaheadSearchResults
/b/userRecommendations/playlistPromotables
/b/users/{userId}/enrollments/courses
/b/users/{userId}/saves
/b/users/{userId}/saves/paginatedPromotables
/b/users/{userId}/saves/sections
/m/episodes/{episodeId}/discussions
/m/episodes/{episodeId}/discussions
/m/episodes/{episodeId}/posts/{postId}/replies
/m/episodes/{episodeId}/posts/{postId}/replies
/m/sneakPreviewAccess/{deviceId}
/m/sneakPreviewStartRequests
/m/trendingSearchTerms
/m/users/{userId}/bookmarks
/m/users/{userId}/bookmarks
/m/users/{userId}/bookmarks/{bookmarkId}
/m/users/{userId}/bookmarks/{bookmarkId}
/m/users/{userId}/episodePosts
/m/users/{userId}/playlistBookmarks
/m/users/{userId}/posts/{postId}
/m/users/{userId}/posts/{postId}
/m/users/{userId}/userPlaylistCursors
/m/users/{userId}/userPlaylistCursors/updateRequests
/m/videos/secure/downloads/episodes/{episodeId}
/m/videos/secure/episodes/{episodeId}
/m/videos/sneakPreview/episodes/{episodeId}
/m/visitors/{visitorId}/visitorPlaylistCursors
/m/visitors/{visitorId}/visitorPlaylistCursors/updateRequests
```
