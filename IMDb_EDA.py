import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.ticker import FuncFormatter

def get_top_100_movies():
    """Retrieve and process top 100 movies from IMDb datasets"""
    # URLs for IMDb datasets
    urls = {
        'basics': "https://datasets.imdbws.com/title.basics.tsv.gz",
        'ratings': "https://datasets.imdbws.com/title.ratings.tsv.gz"
    }
    
    # Load datasets
    basics = pd.read_csv(urls['basics'], sep='\t', compression='gzip')
    ratings = pd.read_csv(urls['ratings'], sep='\t', compression='gzip')
    
    # Merge datasets into one
    movies = basics.merge(ratings, on='tconst')
    
    # Filter and clean data
    movies = movies[movies['titleType'] == 'movie']
    movies = movies.replace('\\N', pd.NA)
    
    # Clean and standardize 'year' and 'runtime' columns - convert 'year' to Int64 for visualization
    movies['startYear'] = (pd.to_numeric(movies['startYear'], errors='coerce').astype('Int64'))  # Capital 'I' for nullable integer
    movies['runtimeMinutes'] = pd.to_numeric(movies['runtimeMinutes'], errors='coerce')
    
    # Sort by votes and select top 100
    movies = movies.sort_values('numVotes', ascending=False).head(100)
    movies.insert(0, 'Rank', range(1, 101))
    
    # Select and rename columns
    movies = movies.rename(columns={
        'primaryTitle': 'Title',
        'startYear': 'Year',
        'averageRating': 'Rating',
        'numVotes': 'Votes',
        'genres': 'Genres',
        'runtimeMinutes': 'Runtime (min)'
    })
    
    return movies[['Rank', 'Title', 'Year', 'Rating', 'Votes', 'Runtime (min)', 'Genres']]

def analyze_data(df):
    """Perform exploratory data analysis (EDA) on movies data"""
    print("\n===== Data Insights =====")
    print(f"Total movies analyzed: {len(df)}")
    print(f"Average rating: {df['Rating'].mean():.1f}")
    print(f"Average runtime: {df['Runtime (min)'].mean():.1f} minutes")
    print(f"Total votes: {df['Votes'].sum():,}")
    
    # Year analysis
    print(f"Oldest movie: {df['Year'].min()} ({df[df['Year'] == df['Year'].min()]['Title'].values[0]})")
    print(f"Newest movie: {df['Year'].max()} ({df[df['Year'] == df['Year'].max()]['Title'].values[0]})")
    
    # Genre analysis
    all_genres = df['Genres'].str.split(',').explode()
    top_genres = all_genres.value_counts().head(3)
    print("\nTop 3 Genres:")
    for genre, count in top_genres.items():
        print(f"- {genre}: {count} movies")

def create_visualizations(df):
    """Create meaningful visualizations of movie data"""
    # Set Seaborn style
    sns.set_style("whitegrid")
    plt.figure(figsize=(16, 12))
    
    # 1. Rating vs. Votes with Runtime
    plt.subplot(2, 2, 1)
    scatter = sns.scatterplot(
        data=df, 
        x='Rating', 
        y='Votes', 
        size='Runtime (min)', 
        hue='Runtime (min)',
        sizes=(50, 300),
        palette='viridis',
        alpha=0.8
    )
    plt.yscale('log')
    plt.title('Rating vs. Votes (Size = Runtime)', fontsize=14)
    plt.xlabel('IMDb Rating', fontsize=12)
    plt.ylabel('Votes (log scale)', fontsize=12)
    
    # Format y-axis for votes
    plt.gca().yaxis.set_major_formatter(FuncFormatter(lambda x, _: f'{x/1e6:.0f}M'))
    
    # Add annotations for top movies
    top_movies = df.nlargest(5, 'Rating')
    for i, row in top_movies.iterrows():
        plt.annotate(
            row['Title'], 
            (row['Rating'], row['Votes']),
            xytext=(5, 5), 
            textcoords='offset points',
            fontsize=9
        )
    
    # 2. Movies by Decade
    plt.subplot(2, 2, 2)
    df['Decade'] = (df['Year'] // 10) * 10
    decade_counts = df['Decade'].value_counts().sort_index()
    sns.barplot(
        x=decade_counts.index.astype(int), 
        y=decade_counts.values, 
        palette='rocket'
    )
    plt.title('Movies by Decade', fontsize=14)
    plt.xlabel('Decade', fontsize=12)
    plt.ylabel('Number of Movies', fontsize=12)
    
    # 3. Rating Distribution by Genre
    plt.subplot(2, 2, 3)
    # Get top 5 genres
    all_genres = df['Genres'].str.split(',').explode()
    top_genres = all_genres.value_counts().head(5).index.tolist()
    
    # Create genre-specific data
    genre_data = []
    for genre in top_genres:
        genre_movies = df[df['Genres'].str.contains(genre)]
        for _, row in genre_movies.iterrows():
            genre_data.append({
                'Genre': genre,
                'Rating': row['Rating']
            })
    
    genre_df = pd.DataFrame(genre_data)
    sns.violinplot(
        x='Genre', 
        y='Rating', 
        data=genre_df, 
        palette='Set2',
        inner='quartile'
    )
    plt.title('Rating Distribution by Top Genres', fontsize=14)
    plt.xlabel('Genre', fontsize=12)
    plt.ylabel('Rating', fontsize=12)
    
    # 4. Runtime Distribution
    plt.subplot(2, 2, 4)
    sns.histplot(
        df['Runtime (min)'], 
        bins=15, 
        kde=True, 
        color='skyblue',
        edgecolor='black'
    )
    plt.title('Runtime Distribution', fontsize=14)
    plt.xlabel('Minutes', fontsize=12)
    plt.ylabel('Number of Movies', fontsize=12)
    plt.axvline(
        df['Runtime (min)'].mean(), 
        color='red', 
        linestyle='dashed', 
        linewidth=1
    )
    plt.text(
        df['Runtime (min)'].mean() + 5, 
        plt.ylim()[1]*0.9, 
        f'Mean: {df["Runtime (min)"].mean():.1f} min', 
        color='red'
    )
    
    plt.tight_layout()
    plt.savefig('movie_analysis.png', dpi=300)
    print("\nSaved visualizations to 'movie_analysis.png'")

def top_movies_by_genre(df):
    """Find top 10 movies in each genre by rating and votes"""
    # Split genres so each movie appears in each of its genres
    genre_df = df.copy()
    genre_df['Genres'] = genre_df['Genres'].str.split(',')
    genre_df = genre_df.explode('Genres')
    
    # Get top 10 movies in each genre by rating
    top_by_rating = genre_df.sort_values(['Genres', 'Rating'], ascending=[True, False])
    top_by_rating = top_by_rating.groupby('Genres').head(10)
    
    # Get top 10 movies in each genre by votes
    top_by_votes = genre_df.sort_values(['Genres', 'Votes'], ascending=[True, False])
    top_by_votes = top_by_votes.groupby('Genres').head(10)
    
    # Create summary for top genres
    print("\n===== Top Movies by Genre =====")
    top_genres = genre_df['Genres'].value_counts().head(3).index
    for genre in top_genres:
        # Top by rating
        rating_top = top_by_rating[top_by_rating['Genres'] == genre].head(3)
        # Top by votes
        votes_top = top_by_votes[top_by_votes['Genres'] == genre].head(3)
        
        print(f"\nTop 3 '{genre}' Movies by Rating:")
        print(rating_top[['Title', 'Rating', 'Year']].to_string(index=False))
        
        print(f"\nTop 3 '{genre}' Movies by Popularity (Votes):")
        print(votes_top[['Title', 'Votes', 'Year']].to_string(index=False))

if __name__ == "__main__":
    print("IMDb Top 100 Movies Analysis")
    print("============================")
    
    # Get data
    print("Downloading and processing data...")
    movies = get_top_100_movies()
    
    # Save to CSV
    movies.to_csv('top_100_imdb_movies.csv', index=False)
    print("\nSaved top 100 movies to 'top_100_imdb_movies.csv'")
    
    # Perform analysis
    analyze_data(movies)
    
    # Create visualizations
    print("\nCreating visualizations...")
    create_visualizations(movies)
    
    # Top movies by genre
    top_movies_by_genre(movies)
    
    print("\nAnalysis complete! Check the generated files.")