import os
import requests
import datetime
import json
from dotenv import load_dotenv
load_dotenv()

# https://developer.themoviedb.org/reference/discover-movie API reference

def fetch_movies():

    api_key = os.getenv('tmdb_api_key')
    filters = [
        "with_origin_country=US",
        
    ]
    sorts = [
        "sort_by=popularity.desc",
    ]
    base_url = "https://api.themoviedb.org/3/discover/movie?{f}&{s}"\
        .format(f="&".join(filters), s="&".join(sorts))

    end_year = datetime.datetime.now().year
    start_year = end_year - 60
    movies = []

    for year in range(start_year, end_year + 1):
        page = 1
        while page <= 5:  # Limit to 100 movies max per year (20 movies per page)
            params = {
                "api_key": api_key,
                "primary_release_year": year,
                "page": page
            }
            response = requests.get(base_url, params=params)
            if response.status_code != 200:
                print(f"Failed to fetch data for {year}, page {page}. Status code: {response.status_code}")
                break

            data = response.json()
            movies.extend(data.get("results", []))

            if page >= data.get("total_pages", 0):
                break
            page += 1

    return movies

def main():
    fields_to_save = set([
        'adult'
        ,'genre_ids'
        ,'id'
        ,'popularity'
        ,'release_date'
        ,'title'
        ,'vote_count'
        ,'vote_average'
        ])
    movies = fetch_movies()
    movies_all = []
    
    # Movie schema
    """
    dim_movies
    ---
    id : int
    title : str
    original_title : str
    release_date : str
    vote_count : int
    vote_average : float
    popularity : float
    adult : bool
    genre_ids : list[int]

    difficulty : enum (vote_count)
    admin_ind_has_clue : bool
    admin_ind_twisted_depri : bool
    """

    for movie in movies:
        
        if movie.get('vote_count') < 2000: continue
        
        # Add basic fields
        filtered_movie = {field: movie.get(field, None) for field in fields_to_save}
        
        # ------ CUSTOM FIELD LOGIC ------ #
        # Movie difficulty
        difficulty = 1
        if movie.get('vote_count', 0) <= 3000: difficulty = 3
        elif movie.get('vote_count', 0) <= 4000: difficulty = 2
        filtered_movie['difficulty'] = difficulty

        ## Admin indicators - Everything defaults to False
        # Does the movie have a clue?
        filtered_movie['admin_ind_has_clue'] = False

        # Should this movie be deprioritized for Twisted Title?
        filtered_movie['admin_ind_twisted_depri'] = False
        
        # add movie to final list
        movies_all.append(filtered_movie)


    # Sort movies within each year by popularity in descending order
    movies_all = sorted(movies_all, key=lambda x: x['vote_count'], reverse=True)
    
    # Write to JSON file
    with open("movies_last_30_years.json", "w") as json_file:
        json.dump(movies_all, json_file, indent=4)

    print("Movies data has been written to 'movies_last_30_years.json'.")

if __name__ == "__main__":
    main()


