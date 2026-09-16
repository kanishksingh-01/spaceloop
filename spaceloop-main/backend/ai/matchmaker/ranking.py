def rank_matches(matches):
    return sorted(matches, key=lambda x: x.get('score', 0), reverse=True)
